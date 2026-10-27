"""Urgency hosting always runs the trusted local model, never invokes AWS."""
from services.urgency.app import create_app

app = create_app(provider='local')
predict = next(route.endpoint for route in app.routes if route.path == '/predict')
ready = next(route.endpoint for route in app.routes if route.path == '/ready')
app.post('/invocations')(predict)
app.api_route('/ping', methods=['GET', 'POST'])(ready)
