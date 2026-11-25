# -*- coding: utf-8 -*-
# (c) 2026 Andreas Motl <andreas.motl@ip-tools.org>
"""
The application registry: Configuration settings, shared service objects,
and the extension points subsystems hook into.

It replaces Pyramid's ``Configurator`` and its component registry. Subsystems
provide a ``setup(registry)`` function, which is invoked by ``registry.include()``.
"""
import importlib
import logging
import typing as t

if t.TYPE_CHECKING:  # pragma: no cover
    from patzilla.web.request import Request
    from patzilla.web.routing import RouteTable
    from patzilla.web.service import Service

logger = logging.getLogger(__name__)


class RequestEvent:
    """
    Passed to request subscribers. Corresponds to Pyramid's ``ContextFound`` event.
    """

    def __init__(self, request: "Request"):
        self.request = request


class RenderEvent(dict):
    """
    Passed to renderer globals subscribers, holding the template namespace.
    Corresponds to Pyramid's ``BeforeRender`` event, which is also a dictionary.
    """

    def __init__(self, system: t.Dict[str, t.Any], rendering_val: t.Any = None):
        super().__init__(system)
        self.rendering_val = rendering_val


class ApplicationEvent:
    """
    Passed to startup hooks. Corresponds to Pyramid's ``ApplicationCreated`` event.
    """

    def __init__(self, app: t.Any, registry: "Registry"):
        self.app = app
        self.registry = registry


class Registry:
    """
    The application registry, also available as ``request.registry``.
    """

    # Configuration settings.
    settings: t.Dict[str, t.Any]
    global_settings: t.Any
    application_settings: t.Any
    datasource_settings: t.Any
    vendor_settings: t.Any
    app_flavor: t.Optional[str]

    # Service objects, populated by subsystems.
    template_renderer: t.Any
    signer: t.Any
    user_metrics_manager: t.Any
    ops_client_pool: t.Any
    ificlaims_client_pool: t.Any
    depatech_client_pool: t.Any
    sip_client_pool: t.Any

    def __init__(self, settings: t.Optional[t.Dict[str, t.Any]] = None):
        self.settings = dict(settings or {})
        self.global_settings = None
        self.application_settings = None
        self.datasource_settings = None
        self.vendor_settings = None
        self.app_flavor = None
        self.template_renderer = None

        self.request_subscribers: t.List[t.Callable[[RequestEvent], None]] = []
        self.renderer_globals: t.List[t.Callable[[RenderEvent], None]] = []
        self.startup_hooks: t.List[t.Callable[[ApplicationEvent], None]] = []
        self.request_methods: t.Dict[str, t.Callable[["Request"], t.Any]] = {}

        # Route tables, static views, and services, in the order they will be matched.
        self.routing: t.List[t.Union["RouteTable", "StaticView", "Service"]] = []

        self._included: t.Set[str] = set()
        self._started = False

    def include(self, target: t.Union[str, t.Callable[["Registry"], None]]) -> None:
        """
        Invoke the ``setup(registry)`` function of a module, or a callable. Modules are included once.
        """
        if callable(target):
            target(self)
            return
        if target in self._included:
            return
        self._included.add(target)
        module = importlib.import_module(target)
        setup = getattr(module, "setup", None)
        if setup is None:
            raise AttributeError(f"Module {target!r} does not provide a `setup(registry)` function")
        setup(self)

    def add_request_subscriber(self, subscriber: t.Callable[[RequestEvent], None]) -> None:
        """
        Register a callable invoked with a ``RequestEvent`` before each request is dispatched
        to its handler. Subscribers are invoked in registration order.
        """
        self.request_subscribers.append(subscriber)

    def add_renderer_globals(self, subscriber: t.Callable[[RenderEvent], None]) -> None:
        """
        Register a callable which can amend the namespace of each rendered template.
        """
        self.renderer_globals.append(subscriber)

    def add_startup_hook(self, hook: t.Callable[[ApplicationEvent], None]) -> None:
        """
        Register a callable invoked once when the application starts.
        """
        self.startup_hooks.append(hook)

    def add_request_method(self, method: t.Callable[["Request"], t.Any], name: t.Optional[str] = None) -> None:
        """
        Register a lazily computed request property. It is computed on first access, then cached.
        """
        self.request_methods[name or method.__name__] = method

    def add_routes(self, table: "RouteTable") -> None:
        """
        Register a table of routes for web pages.
        """
        self.routing.append(table)

    @property
    def services(self) -> t.List["Service"]:
        from patzilla.web.service import Service

        return [entry for entry in self.routing if isinstance(entry, Service)]

    def add_services(self, *services: "Service") -> None:
        """
        Register API services.
        """
        for service in services:
            if service not in self.routing:
                self.routing.append(service)

    def add_services_from(self, module_name: str) -> None:
        """
        Register all API services defined within a module, ordered by attribute name.
        """
        from patzilla.web.service import Service

        module = importlib.import_module(module_name)
        for _, value in sorted(vars(module).items()):
            if isinstance(value, Service):
                self.add_services(value)

    def add_static_view(self, url_path: str, directory: str, cache_max_age: t.Optional[int] = None) -> None:
        """
        Serve static files from a directory, e.g. ``add_static_view("/static", "/path/to/static")``.
        """
        self.routing.append(StaticView(url_path, directory, cache_max_age))

    def notify_request(self, request: "Request") -> None:
        event = RequestEvent(request)
        for subscriber in self.request_subscribers:
            subscriber(event)

    def notify_render(self, system: t.Dict[str, t.Any], value: t.Any = None) -> RenderEvent:
        event = RenderEvent(system, rendering_val=value)
        for subscriber in self.renderer_globals:
            subscriber(event)
        return event

    def notify_startup(self, app: t.Any) -> None:
        """
        Run the startup hooks, once.
        """
        if self._started:
            return
        self._started = True
        event = ApplicationEvent(app=app, registry=self)
        for hook in self.startup_hooks:
            hook(event)


class StaticView:
    def __init__(self, url_path: str, directory: str, cache_max_age: t.Optional[int] = None):
        self.url_path = "/" + url_path.strip("/")
        self.directory = directory
        self.cache_max_age = cache_max_age
