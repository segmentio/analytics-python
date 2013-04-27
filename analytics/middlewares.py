#coding: utf-8

class AnalyticsJSIntector(object):
    """Inject analytics.js snippet on <head>"""
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        return self.app(environ, start_response)
