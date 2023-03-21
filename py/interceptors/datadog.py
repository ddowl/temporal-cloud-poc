from __future__ import annotations
import logging
from typing import Any, Mapping, NoReturn, Optional, Type
from ddtrace import tracer
from ddtrace.context import Context
from temporalio import client, converter, worker, workflow
from temporalio.api.common import v1

logger = logging.getLogger()

TRACE_ID_HEADER_KEY = "trace_id"
SPAN_ID_HEADER_KEY = "span_id"


def marshal_trace_ctx(
    conv: converter.PayloadConverter,
    trace_ctx: Context,
) -> Mapping[str, v1.Payload]:
    return {
        TRACE_ID_HEADER_KEY: conv.to_payloads([trace_ctx.trace_id])[0],
        SPAN_ID_HEADER_KEY: conv.to_payloads([trace_ctx.span_id])[0],
    }


def unmarshal_trace_ctx(
    conv: converter.PayloadConverter, headers: Mapping[str, v1.Payload]
) -> Optional[Context]:
    marshalled_trace_id = headers.get(TRACE_ID_HEADER_KEY)
    marshalled_span_id = headers.get(SPAN_ID_HEADER_KEY)

    if not marshalled_trace_id or not marshalled_span_id:
        return None

    trace_ctx = Context()
    trace_ctx.trace_id = conv.from_payloads([marshalled_trace_id])[0]
    trace_ctx.span_id = conv.from_payloads([marshalled_span_id])[0]
    return trace_ctx


def inject_trace_ctx_headers(
    conv: converter.PayloadConverter, headers: Mapping[str, v1.Payload]
) -> Mapping[str, v1.Payload]:
    ctx = tracer.current_trace_context()
    logger.debug("trace context: %s", ctx)
    return {**headers, **marshal_trace_ctx(conv, ctx)} if ctx is not None else headers


class DatadogInterceptor(client.Interceptor, worker.Interceptor):
    """Interceptor that supports client and worker Datadog span creation
    and propagation.

    This should be created and used for ``interceptors`` on the
    :py:meth:`temporalio.client.Client.connect` call to apply to all client
    calls and worker calls using that client. To only apply to workers, set as
    worker creation option instead of in client.
    """

    def __init__(
        self, payload_converter: converter.PayloadConverter = converter.PayloadConverter.default
    ) -> None:
        """Initialize a Datadog tracing interceptor."""

        logger.debug("Initializing DatadogInterceptor")
        self.payload_converter = payload_converter

    def intercept_client(self, next: client.OutboundInterceptor) -> client.OutboundInterceptor:
        return _DatadogClientOutboundInterceptor(next, self)

    def intercept_activity(
        self, next: worker.ActivityInboundInterceptor
    ) -> worker.ActivityInboundInterceptor:
        return _DatadogActivityInboundInterceptor(next, self)

    def workflow_interceptor_class(
        self, input: worker.WorkflowInterceptorClassInput
    ) -> Type[DatadogWorkflowInboundInterceptor]:
        return DatadogWorkflowInboundInterceptor


class _DatadogClientOutboundInterceptor(client.OutboundInterceptor):
    def __init__(self, next: client.OutboundInterceptor, root: DatadogInterceptor) -> None:
        logger.debug("Initializing _DatadogClientOutboundInterceptor")
        super().__init__(next)
        self.root = root

    async def start_workflow(
        self, input: client.StartWorkflowInput
    ) -> client.WorkflowHandle[Any, Any]:
        logger.debug("_DatadogClientOutboundInterceptor intercepting start_workflow")
        input.headers = inject_trace_ctx_headers(self.root.payload_converter, input.headers)
        return await super().start_workflow(input)

    async def query_workflow(self, input: client.QueryWorkflowInput) -> Any:
        logger.debug("_DatadogClientOutboundInterceptor intercepting query_workflow")
        input.headers = inject_trace_ctx_headers(self.root.payload_converter, input.headers)
        return await super().query_workflow(input)

    async def signal_workflow(self, input: client.SignalWorkflowInput) -> None:
        logger.debug("_DatadogClientOutboundInterceptor intercepting signal_workflow")
        input.headers = inject_trace_ctx_headers(self.root.payload_converter, input.headers)
        return await super().signal_workflow(input)


class _DatadogActivityInboundInterceptor(worker.ActivityInboundInterceptor):
    def __init__(self, next: worker.ActivityInboundInterceptor, root: DatadogInterceptor) -> None:
        logger.debug("Initializing _DatadogActivityInboundInterceptor")
        super().__init__(next)
        self.root = root

    async def execute_activity(self, input: worker.ExecuteActivityInput) -> Any:
        logger.debug("_DatadogActivityInboundInterceptor intercepting execute_activity")
        ctx = unmarshal_trace_ctx(self.root.payload_converter, input.headers)
        tracer.context_provider.activate(ctx)
        await super().execute_activity(input)


class DatadogWorkflowInboundInterceptor(worker.WorkflowInboundInterceptor):
    """Datadog interceptor for inbound workflow calls."""

    def __init__(self, next: worker.WorkflowInboundInterceptor) -> None:
        """Initialize a tracing workflow interceptor."""
        logger.debug("Initializing DatadogWorkflowInboundInterceptor")
        super().__init__(next)

        self.payload_converter = converter.PayloadConverter.default

    def init(self, outbound: worker.WorkflowOutboundInterceptor) -> None:
        super().init(_DatadogWorkflowOutboundInterceptor(outbound, self))

    async def execute_workflow(self, input: worker.ExecuteWorkflowInput) -> Any:
        logger.debug("DatadogWorkflowInboundInterceptor intercepting execute_workflow")
        ctx = unmarshal_trace_ctx(self.payload_converter, input.headers)
        tracer.context_provider.activate(ctx)
        return await super().execute_workflow(input)

    async def handle_signal(self, input: worker.HandleSignalInput) -> None:
        logger.debug("DatadogWorkflowInboundInterceptor intercepting handle_signal")
        ctx = tracer.current_trace_context()
        tracer.context_provider.activate(ctx)
        await super().handle_signal(input)

    async def handle_query(self, input: worker.HandleQueryInput) -> Any:
        logger.debug("DatadogWorkflowInboundInterceptor intercepting handle_query")
        ctx = tracer.current_trace_context()
        tracer.context_provider.activate(ctx)
        return await super().handle_query(input)


class _DatadogWorkflowOutboundInterceptor(worker.WorkflowOutboundInterceptor):
    def __init__(
        self,
        next: worker.WorkflowOutboundInterceptor,
        root: DatadogWorkflowInboundInterceptor,
    ) -> None:
        logger.debug("initializing _DatadogWorkflowOutboundInterceptor")
        super().__init__(next)
        self.root = root

    def continue_as_new(self, input: worker.ContinueAsNewInput) -> NoReturn:
        logger.debug("_DatadogWorkflowOutboundInterceptor intercepting continue_as_new")
        input.headers = inject_trace_ctx_headers(self.root.payload_converter, input.headers)
        super().continue_as_new(input)

    async def signal_child_workflow(self, input: worker.SignalChildWorkflowInput) -> None:
        logger.debug("_DatadogWorkflowOutboundInterceptor intercepting signal_child_workflow")
        input.headers = inject_trace_ctx_headers(self.root.payload_converter, input.headers)
        await super().signal_child_workflow(input)

    async def signal_external_workflow(self, input: worker.SignalExternalWorkflowInput) -> None:
        logger.debug("_DatadogWorkflowOutboundInterceptor intercepting signal_external_workflow")
        input.headers = inject_trace_ctx_headers(self.root.payload_converter, input.headers)
        await super().signal_external_workflow(input)

    def start_activity(self, input: worker.StartActivityInput) -> workflow.ActivityHandle:
        logger.debug("_DatadogWorkflowOutboundInterceptor intercepting start_activity")
        input.headers = inject_trace_ctx_headers(self.root.payload_converter, input.headers)
        return super().start_activity(input)

    async def start_child_workflow(
        self, input: worker.StartChildWorkflowInput
    ) -> workflow.ChildWorkflowHandle:
        logger.debug("_DatadogWorkflowOutboundInterceptor intercepting start_child_workflow")
        input.headers = inject_trace_ctx_headers(self.root.payload_converter, input.headers)
        return await super().start_child_workflow(input)

    def start_local_activity(
        self, input: worker.StartLocalActivityInput
    ) -> workflow.ActivityHandle:
        logger.debug("_DatadogWorkflowOutboundInterceptor intercepting start_local_activity")
        input.headers = inject_trace_ctx_headers(self.root.payload_converter, input.headers)
        return super().start_local_activity(input)
