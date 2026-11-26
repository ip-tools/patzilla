# -*- coding: utf-8 -*-
# (c) 2026 Andreas Motl <andreas.motl@ip-tools.org>
"""
PatZilla's web application, based on FastAPI. The concepts of the former Pyramid/Cornice
implementation map like this:

- Registry and ZCA utilities  -> `AppState` in `app.state.patzilla`, created within the lifespan
- `ContextFound` subscribers  -> dependencies, see `patzilla.web.dependencies`
- `attach_user` subscriber    -> `SessionAuthMiddleware`, populating `request.user`
- `pyramid.threadlocal`       -> upstream clients are passed explicitly into the access layer
- Cornice services            -> `APIRouter`s with typed parameters
- `request.errors`            -> `ServiceError` exceptions, rendered as JSON error envelope
- Renderers, `BeforeRender`   -> `Response` classes, `patzilla.web.templating.Page`
- PasteDeploy, `pserve`       -> `WebSettings` from the INI file, `patzilla serve` (uvicorn)
"""
