"""Check the ppt_spec contract against the committed template, and smoke-test the fill verbs."""
import sys

sys.stdout.reconfigure(encoding="utf-8")
from app.engine.pptx_fill import (  # noqa: E402
    contract_names,
    fill_table,
    layout_for,
    layout_shape_names,
    open_template,
    replace_chart_data,
    resolve_shape,
    set_text,
)
from app.engine.pptx_fill.ppt_spec import DECK_SLIDES  # noqa: E402

prs = open_template()
ok = True
for slide_id in DECK_SLIDES:
    layout_name = layout_for(slide_id)
    on_layout = set(layout_shape_names(prs, layout_name))
    contract = contract_names(slide_id)
    missing = sorted(contract - on_layout)
    unused = sorted(on_layout - contract)
    print(f"{slide_id} ({layout_name}): contract={len(contract)} layout={len(on_layout)}")
    if missing:
        ok = False
        print("   MISSING FROM TEMPLATE:", missing)
    if unused:
        print("   not in contract (carries no data):", unused)
print("CONTRACT OK" if ok else "CONTRACT BROKEN")