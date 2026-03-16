from __future__ import annotations
import math

def heat_index_c(temp_c: float, rh: float) -> float:
    # Convert to F for the classic formula, then back to C.
    t_f = temp_c * 9/5 + 32
    hi_f = (
        -42.379 + 2.04901523*t_f + 10.14333127*rh
        - 0.22475541*t_f*rh - 0.00683783*t_f*t_f
        - 0.05481717*rh*rh + 0.00122874*t_f*t_f*rh
        + 0.00085282*t_f*rh*rh - 0.00000199*t_f*t_f*rh*rh
    )
    hi_c = (hi_f - 32) * 5/9
    if math.isnan(hi_c) or math.isinf(hi_c):
        return temp_c
    return float(hi_c)
