# X-Step inference API

```bash
python -m api.main
```

OpenAPI: http://127.0.0.1:8080/docs

The mobile app calls this when `EXPO_PUBLIC_XSTEP_API` is set. If the server is unreachable, the app falls back to the on-device gait engine.
