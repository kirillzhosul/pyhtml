# PyHTML
Write HTML in Python and run it!

### Example:
```py
from pyhtml import UIComponent, UIApp

ui = UIApp()

ui.style(".mystyle", {"color": "green"})

ui.span("colored text", style="color: red")
ui.span("colored text", properties={"class": "mystyle"})
ui.div(
    [
        UIComponent(data="div el 1", tag="span"),
        UIComponent(data="div el 2", tag="span"),
    ]
)
ui.add_component(UIComponent(data=None, tag="hr"))
ui.button("click me", onClick="alert(1)")

ui.run()
```

### Build to static:
```py
# Just use `build` instead of `run`
ui.build()
```
