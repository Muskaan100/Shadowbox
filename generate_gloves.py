import cv2
import numpy as np
import math

def draw_reference_glove(width=360, height=480, is_left=True):
    """
    Generate high-resolution RGBA boxing glove sprite precisely matching
    the user's reference image illustration.
    """
    img = np.zeros((height, width, 4), dtype=np.uint8)

    # Reference image color palette (BGRA)
    c_outline = (22, 10, 115, 255)       # #730A16 Deep burgundy outline
    c_fill = (45, 42, 235, 255)          # #EB2A2D Vibrant boxing red
    c_shadow = (25, 20, 175, 255)        # #AF1419 Deep leather shadow
    c_highlight = (130, 120, 255, 255)   # #FF7882 Soft specular leather highlight
    c_highlight_subtle = (90, 85, 245, 255)
    c_strap = (38, 35, 222, 255)         # Wrist strap base
    c_strap_shadow = (25, 18, 160, 255)
    c_stitch = (22, 10, 115, 255)        # Stitch line color

    # We draw in a normalized coordinate space (0..1) then scale to (width, height)
    # The reference glove (back-of-hand / dorsal view):
    # Thumb is on the right for the left glove (medial side)
    
    def P(x, y):
        # x: 0..1, y: 0..1
        if not is_left:
            x = 1.0 - x
        return (int(x * width), int(y * height))

    # 1. Main Glove Fist Body Contour Points
    # Top knuckle curve, tapering down to wrist, with thumb notch on the right
    body_curve = [
        P(0.18, 0.22), P(0.20, 0.16), P(0.25, 0.11), P(0.33, 0.07), P(0.44, 0.06),
        P(0.55, 0.07), P(0.64, 0.10), P(0.70, 0.15), P(0.73, 0.22),
        P(0.74, 0.32), P(0.73, 0.44), P(0.70, 0.54), P(0.66, 0.65), P(0.65, 0.72),
        P(0.28, 0.72), P(0.27, 0.64), P(0.24, 0.52), P(0.20, 0.40), P(0.18, 0.30)
    ]
    body_pts = np.array(body_curve, np.int32)

    # 2. Thumb Section Contour Points
    # Protrudes from right side (for left glove), rounded curved tip pointing up
    thumb_curve = [
        P(0.70, 0.38), P(0.75, 0.32), P(0.82, 0.30), P(0.88, 0.33), P(0.92, 0.40),
        P(0.92, 0.50), P(0.88, 0.62), P(0.82, 0.70), P(0.75, 0.74), P(0.66, 0.72),
        P(0.68, 0.60), P(0.70, 0.50), P(0.71, 0.42)
    ]
    thumb_pts = np.array(thumb_curve, np.int32)

    # 3. Wrist Cuff Trapezoid Points
    cuff_curve = [
        P(0.26, 0.72), P(0.66, 0.72),
        P(0.70, 0.94), P(0.29, 0.94)
    ]
    cuff_pts = np.array(cuff_curve, np.int32)

    # 4. Velcro Strap Points (wrapped across wrist)
    strap_curve = [
        P(0.27, 0.75), P(0.67, 0.75),
        P(0.69, 0.90), P(0.28, 0.90)
    ]
    strap_pts = np.array(strap_curve, np.int32)

    # Bottom rolled rim of cuff
    rim_curve = [
        P(0.29, 0.93), P(0.70, 0.93),
        P(0.69, 0.96), P(0.30, 0.96)
    ]
    rim_pts = np.array(rim_curve, np.int32)

    # RENDER LAYERS WITH HIGH-QUALITY ANTI-ALIASING:

    # A. Draw Wrist Cuff Background
    cv2.fillPoly(img, [cuff_pts], c_fill)
    cv2.polylines(img, [cuff_pts], True, c_outline, 8, cv2.LINE_AA)

    # B. Draw Thumb Base & Shadow
    cv2.fillPoly(img, [thumb_pts], c_shadow)
    # Inner thumb fill (slightly inset)
    thumb_inner_curve = [
        P(0.71, 0.40), P(0.76, 0.34), P(0.82, 0.33), P(0.87, 0.36), P(0.89, 0.42),
        P(0.89, 0.51), P(0.85, 0.61), P(0.80, 0.68), P(0.74, 0.70), P(0.68, 0.68),
        P(0.70, 0.52)
    ]
    cv2.fillPoly(img, [np.array(thumb_inner_curve, np.int32)], c_fill)

    # C. Draw Main Fist Body Fill
    cv2.fillPoly(img, [body_pts], c_fill)

    # D. Leather Shadow on bottom & lateral edges of main body
    shadow_curve = [
        P(0.55, 0.08), P(0.64, 0.11), P(0.70, 0.16), P(0.73, 0.23),
        P(0.74, 0.33), P(0.73, 0.44), P(0.70, 0.54), P(0.66, 0.65), P(0.65, 0.72),
        P(0.52, 0.72), P(0.56, 0.55), P(0.59, 0.40), P(0.58, 0.25), P(0.53, 0.15)
    ]
    cv2.fillPoly(img, [np.array(shadow_curve, np.int32)], c_shadow)

    # E. Smooth Leather Specular Highlight (Curved light patch on top-left knuckle)
    highlight_curve = [
        P(0.25, 0.17), P(0.30, 0.12), P(0.38, 0.09), P(0.48, 0.09),
        P(0.54, 0.12), P(0.52, 0.17), P(0.44, 0.16), P(0.34, 0.17),
        P(0.28, 0.22), P(0.24, 0.28), P(0.23, 0.22)
    ]
    cv2.fillPoly(img, [np.array(highlight_curve, np.int32)], c_highlight)

    # Secondary soft highlight curve
    highlight_sub_curve = [
        P(0.22, 0.28), P(0.25, 0.22), P(0.28, 0.30), P(0.27, 0.42),
        P(0.23, 0.48), P(0.21, 0.38)
    ]
    cv2.fillPoly(img, [np.array(highlight_sub_curve, np.int32)], c_highlight_subtle)

    # Thumb specular highlight
    thumb_hl_curve = [
        P(0.78, 0.34), P(0.83, 0.33), P(0.87, 0.36), P(0.88, 0.42),
        P(0.86, 0.48), P(0.83, 0.44), P(0.80, 0.38)
    ]
    cv2.fillPoly(img, [np.array(thumb_hl_curve, np.int32)], c_highlight)

    # F. Outlines
    # Main body outline
    cv2.polylines(img, [body_pts], True, c_outline, 8, cv2.LINE_AA)
    # Thumb outline & separation seam
    cv2.polylines(img, [thumb_pts], True, c_outline, 8, cv2.LINE_AA)

    # G. Wrist Velcro Strap & Detailing
    cv2.fillPoly(img, [strap_pts], c_strap)
    cv2.polylines(img, [strap_pts], True, c_outline, 7, cv2.LINE_AA)

    # Double stitch lines at the strap closure
    stitch_x1 = 0.62 if is_left else 0.38
    stitch_x2 = 0.64 if is_left else 0.36
    cv2.line(img, P(stitch_x1, 0.77), P(stitch_x1, 0.88), c_stitch, 3, cv2.LINE_AA)
    cv2.line(img, P(stitch_x2, 0.77), P(stitch_x2, 0.88), c_stitch, 3, cv2.LINE_AA)

    # Horizontal seam along bottom of strap
    cv2.line(img, P(0.28, 0.90), P(0.69, 0.90), c_outline, 4, cv2.LINE_AA)

    # Rolled bottom hem of cuff
    cv2.fillPoly(img, [rim_pts], c_strap_shadow)
    cv2.polylines(img, [rim_pts], True, c_outline, 6, cv2.LINE_AA)

    # Thumb inner seam crease accent (giving the tucked look from the reference)
    seam_pts = [P(0.70, 0.38), P(0.69, 0.48), P(0.67, 0.58), P(0.66, 0.68)]
    cv2.polylines(img, [np.array(seam_pts, np.int32)], False, c_outline, 5, cv2.LINE_AA)

    return img

if __name__ == "__main__":
    g_left = draw_reference_glove(width=360, height=480, is_left=True)
    g_right = draw_reference_glove(width=360, height=480, is_left=False)
    cv2.imwrite("boxing_glove_left.png", g_left)
    cv2.imwrite("boxing_glove_right.png", g_right)
    print("Reference boxing glove sprites generated successfully!")
