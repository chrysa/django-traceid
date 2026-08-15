# Deep-dive: `chrysa/django-traceid`

**Purpose (1 phrase).** Une lib Django project-agnostique et zero-config qui propage un
`trace_id` de bout en bout (HTTP → logging → jobs RQ/Celery → pub/sub) via
`contextvars.ContextVar`, enrichissant chaque ligne de log sans monkey-patching.

**Stack observée.** `src/django_traceid/` (~90 lignes runtime) : `context.py` (ContextVar +
`trace_context`), `middleware.py` (`TraceIdMiddleware`, réutilise/génère `X-Request-ID`,
tag Sentry optionnel lazy), `filters.py` (`TraceIdFilter` stdlib logging filter),
`conf.py` (settings `TRACEID`), `rq.py` (`enqueue_with_trace`, `trace_aware`,
`restore_trace_context` cross-process). Python 3.12+ (PEP 695 generics), Django 4.2+, MIT.

Le projet est **une lib d'observabilité mature qui a déjà des équivalents OSS directs** —
c'est le cas idéal d'un teardown comparatif : les 3 réfs ci-dessous couvrent exactement le
même problème avec des choix de design proches. Peu de sources supplémentaires apporteraient
de la valeur.

---

## snok/django-guid

- **owner/repo** : `snok/django-guid`
- **stars** : ~484
- **activité** : actif (212+ commits, mainteneur snok/organisation active)
- **licence** : **MIT** ✅ (copiable)
- **fichier/module du pattern** : `django_guid/middleware.py`, `django_guid/log_filters.py`,
  `django_guid/context.py` (ContextVar), `django_guid/integrations/` (Sentry, Celery)
- **mécanisme réel** : GUID stocké dans un `ContextVar` (depuis >=3.0.0), posé par le
  middleware au début de la requête, lu par un logging filter `CorrelationId`. Système
  d'**intégrations pluggables** (`SentryIntegration`, `CeleryIntegration`) enregistrées via
  le setting `DJANGO_GUID = {"INTEGRATIONS": [...]}`. `VALIDATE_GUID` valide le format UUID
  entrant ; `RETURN_HEADER` renvoie le GUID dans la réponse.
- **snippet portable (~15 lignes)** — le pattern d'intégrations enregistrables, que
  django-traceid n'a pas (il a juste un `SENTRY_TAG` booléen) :

  ```python
  class Integration:
      identifier: str  # unique name
      def setup(self): ...          # called once at app ready
      def run(self, guid, **kwargs): ...  # called per-request with the id

  class SentryIntegration(Integration):
      identifier = "SentryIntegration"
      def run(self, guid, **kwargs):
          import sentry_sdk
          sentry_sdk.set_tag("transaction_id", guid)

  # settings: TRACEID = {"INTEGRATIONS": [SentryIntegration(), CeleryIntegration()]}
  # middleware loops: for i in settings.integrations: i.run(trace_id)
  ```

- **étapes d'intégration dans ce projet** :
  1. Généraliser le `SENTRY_TAG: bool` de `conf.py`/`middleware.py` en une liste
     `INTEGRATIONS` d'objets exposant `run(trace_id)`.
  2. Fournir `SentryIntegration` et `CeleryIntegration` (signal `task_prerun`/`task_postrun`)
     out-of-the-box, en gardant l'import lazy déjà en place.
  3. Reprendre l'option `VALIDATE_GUID` : django-traceid a `INCOMING_MAX_LENGTH` mais pas de
     validation de forme UUID → ajouter un `VALIDATE_INCOMING` optionnel.
- **gotchas** : django-guid impose son propre header/format ; ne pas casser le contrat
  duck-typed de django-traceid (pas de dépendance dure à Celery/Sentry). L'approche
  "integration objects" ajoute de la surface d'API — à peser vs. la philosophie "5 moving
  parts". Copiable tel quel (MIT) mais préférer réimplémenter au style PEP 695 du repo.

---

## dabapps/django-log-request-id

- **owner/repo** : `dabapps/django-log-request-id`
- **stars** : ~384
- **activité** : mature/stable (170+ commits ; le projet de référence historique du pattern)
- **licence** : **BSD-2-Clause** ✅ (copiable, attribution)
- **fichier/module du pattern** : `log_request_id/middleware.py` (`RequestIDMiddleware`),
  `log_request_id/filters.py` (`RequestIDFilter`), stockage `ContextVar`
- **mécanisme réel** : middleware génère/récupère l'id, l'attache à la fois au `ContextVar`
  ET à `request.id` (accès applicatif direct), un `RequestIDFilter` l'injecte dans les
  LogRecords. Point distinctif : **request logging complet** — option pour logger chaque
  requête entrante avec méthode, path, user id, status, en une ligne structurée
  (`LOG_REQUESTS = True`), plus `OUTGOING_REQUEST_ID_HEADER` pour propager l'id aux appels
  HTTP sortants.
- **snippet portable (~12 lignes)** — la ligne de log de requête complète, absente de
  django-traceid :

  ```python
  # settings: TRACEID = {"LOG_REQUESTS": True}
  class TraceLoggingMiddleware:
      def __call__(self, request):
          response = self.get_response(request)
          if getattr(settings, "LOG_REQUESTS", False):
              logger.info("request", extra={
                  "method": request.method, "path": request.path,
                  "status": response.status_code,
                  "user_id": getattr(request.user, "id", None),
              })  # trace_id added automatically by the filter
          return response
  ```

- **étapes d'intégration dans ce projet** :
  1. Ajouter un flag `LOG_REQUESTS` optionnel émettant une ligne de synthèse par requête
     (le `trace_id` est déjà injecté par `TraceIdFilter`, donc corrélable).
  2. Exposer `request.trace_id` en plus du ContextVar pour l'accès applicatif sans import
     (django-log-request-id le fait, django-traceid oblige à appeler `get_trace_id()`).
  3. Considérer `OUTGOING_*_HEADER` : helper pour injecter le `trace_id` dans les headers
     d'un `requests`/`httpx` sortant (compagnon naturel du `rq.py`).
- **gotchas** : BSD-2 = garder la notice de copyright si on copie littéralement du code ;
  ici on réimplémente donc pas d'obligation. Le `request.id` global peut fuiter entre
  requêtes async si mal fait — django-traceid a raison de rester ContextVar-only ; n'ajouter
  `request.trace_id` que comme miroir en lecture.

---

## watchingwhileusleep/x-request-id-middleware

- **owner/repo** : `watchingwhileusleep/x-request-id-middleware`
- **stars** : ~2 (jeune, faible adoption — retenu pour l'angle **multi-framework**)
- **activité** : jeune (13 commits)
- **licence** : **MIT** ✅ (copiable)
- **fichier/module du pattern** : middleware Django `XRequestIDMiddleware` + FastAPI
  `FastAPIXRequestIDMiddleware`, accès via `get_x_request_id()`, extras `[django]`/`[fastapi]`
- **mécanisme réel** : même socle `contextvars`, mais **une seule lib pour Django ET
  FastAPI** avec extras d'install optionnels ; tag Sentry + propagation header NGINX.
- **snippet portable (~10 lignes)** — packaging à extras framework-agnostique :

  ```toml
  # pyproject.toml
  [project.optional-dependencies]
  django  = ["Django>=4.2"]
  fastapi = ["starlette>=0.37"]
  # core (context.py) stays dependency-free; frameworks are opt-in extras
  ```

- **étapes d'intégration dans ce projet** :
  1. `context.py` est déjà 100% dépendance-free → il pourrait devenir le cœur d'un package
     `traceid` avec django comme extra, ouvrant la porte à un adaptateur FastAPI/Starlette.
  2. Si un jour un besoin FastAPI apparaît dans le fleet, réutiliser ce découpage core/extras
     plutôt que dupliquer la logique ContextVar.
- **gotchas** : très faible maturité (2 stars, 13 commits) → **ne pas dépendre**, seulement
  s'inspirer du découpage packaging. django-traceid est déjà plus complet et mieux typé.

---

## Synthèse licences

Toutes permissives : **MIT** (django-guid, x-request-id-middleware) et **BSD-2-Clause**
(django-log-request-id) — toutes copiables. Aucune source copyleft/restrictive (pas de
GPL/AGPL/BSL/Elastic). BSD-2 impose seulement de conserver la notice si on copie du code
verbatim ; ici on réimplémente au style PEP 695 du repo, donc aucune contrainte bloquante.

## Recommandations priorisées (quick-wins first)

1. **`request.trace_id` en lecture** (miroir du ContextVar) — trivial, ergonomie (ex.
   django-log-request-id).
2. **`LOG_REQUESTS` opt-in** — 1 ligne de synthèse/requête, déjà corrélée par le filter.
3. **`VALIDATE_INCOMING`** — validation de forme en plus du `INCOMING_MAX_LENGTH` (django-guid).
4. **Integrations pluggables** (moyen) — généraliser `SENTRY_TAG` → liste d'intégrations
   (Sentry, Celery) façon django-guid, sans dépendance dure.
