"""
    Create HTML inside Python and serve it.
"""


from typing import TypeAlias, Any
from functools import lru_cache

from fastapi.responses import HTMLResponse
from fastapi import FastAPI

PROPERTIES: TypeAlias = dict[str, Any]


def _render_properties(properties: PROPERTIES):
    rendered_properties = []
    for key, value in properties.items():
        if isinstance(value, str):
            value = f'"{value}"'

        rendered_properties.append(f"{key}={value}")
    return " ".join(rendered_properties)


class UIComponent:
    def __init__(
        self,
        data: Any | None,
        tag: str | None = None,
        properties: PROPERTIES | None = None,
    ) -> None:
        self.data = data
        self.properties = properties
        self.tag = tag

    def render(self) -> str:
        rendered_body = (
            [self.data]
            if not isinstance(self.data, list) and self.data is not None
            else []
        )

        if isinstance(self.data, list):
            for component in self.data:
                if not isinstance(component, UIComponent):
                    raise ValueError(
                        f"Expected UIComponent nested data to contain list of UIComponents but got {type(component)}"
                    )
                rendered_body.append(component.render())

        properties = _render_properties(self.properties) if self.properties else ""
        return f"<{self.tag} {properties}>{''.join(rendered_body)}</{self.tag}>"


class UIApp:
    def __init__(self) -> None:
        self._pregenerated_styles = {}
        self._components: list[UIComponent] = []

    def add_component(self, component: UIComponent):
        self._components.append(component)

    def span(
        self, data: Any | None = None, properties: PROPERTIES | None = None, **kwargs
    ):
        properties = (kwargs | properties) if properties is not None else kwargs
        self.add_component(UIComponent(data=data, tag="span", properties=properties))

    def button(
        self, data: Any | None = None, properties: PROPERTIES | None = None, **kwargs
    ):
        properties = (kwargs | properties) if properties is not None else kwargs
        self.add_component(UIComponent(data=data, tag="button", properties=properties))

    def div(
        self, data: Any | None = None, properties: PROPERTIES | None = None, **kwargs
    ):
        properties = (kwargs | properties) if properties is not None else kwargs
        self.add_component(UIComponent(data=data, tag="div", properties=properties))

    def style(self, selector: str, properties: PROPERTIES | None = None):
        self._pregenerated_styles[selector] = properties

    def _render_components(self):
        rendered_body = ""
        for component in self._components:
            rendered_body += component.render()
        return rendered_body

    @lru_cache(maxsize=128)
    def _render_pregenerated_styles(self):
        rendered_styles = []
        for selector, properties in self._pregenerated_styles.items():
            style_body = []
            for key, value in properties.items():
                style_body.append(f"{key}: {value}")
            rendered_styles.append(f"{selector}" + "{" + ",\n".join(style_body) + "}")

        return "\n".join(rendered_styles)

    def _generate_html_content(self):
        return f"""
            <html>
                <head>
                    <title>PyHTML</title>
                    <style>{self._render_pregenerated_styles()}</style>
                </head>
                <body>
                    { self._render_components()}
                </body>
            </html>
        """

    def _route_handler(self):
        html_content = self._generate_html_content()
        return HTMLResponse(html_content, status_code=200)

    def run(self):
        import uvicorn

        app = FastAPI()
        app.add_api_route("/", self._route_handler)
        uvicorn.run(app)

    def build(self):
        with open("./index.html", mode="w") as f:
            f.write(self._generate_html_content())
