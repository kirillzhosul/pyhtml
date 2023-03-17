"""
    Create HTML inside Python and serve it.
"""

from typing import TypeAlias, Any
from functools import lru_cache

from fastapi.responses import HTMLResponse
from fastapi import FastAPI

PROPERTIES: TypeAlias = dict[str, Any]


def _render_properties(properties: PROPERTIES) -> str:
    """
    Renders properties into HTML properties string.
    """
    rendered_properties = []
    for key, value in properties.items():
        if isinstance(value, str):
            value = f'"{value}"'

        rendered_properties.append(f"{key}={value}")
    return " ".join(rendered_properties)


class UIComponent:
    """
    Base component for all tags.
    """

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
        """
        Renders component into HTML tag.
        """
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


class _BaseUIApp:
    """
    Base UIApp that handles private stuff with rendering and serving.
    """

    def __init__(self) -> None:
        self._pregenerated_styles: dict[str, PROPERTIES] = {}
        self._components: list[UIComponent] = []

        self._default_title = "Built with PyHTML!"

    @lru_cache(maxsize=1)
    def _render_components(self) -> str:
        """
        Renders all components into HTML.
        """
        return ["".join([component.render() for component in self._components])]

    @lru_cache(maxsize=1)
    def _render_pregenerated_styles(self) -> str:
        """
        Returns styles rendered in CSS.
        """
        rendered_styles = []
        for selector, properties in self._pregenerated_styles.items():
            style_body = []
            for key, value in properties.items():
                style_body.append(f"{key}: {value}")
            rendered_styles.append(f"{selector}" + "{" + ",\n".join(style_body) + "}")

        return "\n".join(rendered_styles)

    def _generate_html_content(self) -> str:
        """
        Generates HTML response content with all styles and body.
        """
        return f"""
<html>
    <head>
        <title>{self._default_title}</title>
        <style>{self._render_pregenerated_styles()}</style>
    </head>
    <body>
        { self._render_components()}
    </body>
</html>
        """

    def _route_handler(self) -> HTMLResponse:
        """
        Route handler for the FastAPI app.
        """
        return HTMLResponse(self._generate_html_content(), status_code=200)


class _UIAppTagsShortcutMixin:
    """
    Mixin for the UIApp that adds shortcuts for tags.
    """

    def _tag_shortcut(
        self,
        tag: str,
        data: Any | None = None,
        properties: PROPERTIES | None = None,
        **kwargs,
    ):
        properties = (kwargs | properties) if properties is not None else kwargs
        self.add_component(UIComponent(data=data, tag="span", properties=properties))

    def span(
        self, data: Any | None = None, properties: PROPERTIES | None = None, **kwargs
    ):
        self._tag_shortcut("span", data, properties, **kwargs)

    def button(
        self, data: Any | None = None, properties: PROPERTIES | None = None, **kwargs
    ):
        self._tag_shortcut("button", data, properties, **kwargs)

    def div(
        self, data: Any | None = None, properties: PROPERTIES | None = None, **kwargs
    ):
        self._tag_shortcut("div", data, properties, **kwargs)


class UIApp(_BaseUIApp, _UIAppTagsShortcutMixin):
    def add_component(self, component: UIComponent) -> None:
        """
        Adds raw component to list of all components.
        """
        self._components.append(component)

    def style(self, selector: str, properties: PROPERTIES) -> None:
        """
        Adds style for the given selector by overwriting it.
        """
        self._pregenerated_styles[selector] = properties

    def run(self) -> None:
        """
        Starts FastAPI with Uvicorn ASGI.

        You can also try to use `build` to create static files and serve by your own.
        """
        import uvicorn

        app = FastAPI()
        app.add_api_route("/", self._route_handler)
        # TODO: Add multi routes.

        uvicorn.run(app)
        del uvicorn

    def build(self, directory: str = "./") -> None:
        """
        Creates packed static files that can served with static server.
        """
        with open(f"{directory}index.html", mode="w") as f:
            f.write(self._generate_html_content())
