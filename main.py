import streamlit as st
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches  # Import patches explicitly
from typing import Dict, List, Any

# Set page config
st.set_page_config(
    page_title="Nesting Calculator”",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title and introduction
st.title("Nesting Calculator")
st.markdown("""
This application calculates how many shapes of a given type can fit onto a sheet
with specified dimensions, considering clearance between shapes.
""")

# Functions from original code
def pack_shapes(shape_type: str, params: Dict[str, float], num_shapes: int, 
                sheet_w: float, sheet_h: float, clearance: float = 0.0) -> List[List[Dict[str, Any]]]:
    """
    Pack up to `num_shapes` of a given type onto multiple sheets.
    Returns a list of sheets; each sheet is a list of dicts:
      {'type': str, 'params': dict, 'x': float, 'y': float}
    """
    placed = 0
    sheets = []

    # Determine grid increments per shape
    if shape_type == 'circle':
        r = params['r']
        D_eff = 2*r + clearance
        dx = D_eff
        dy = D_eff * math.sqrt(3) / 2
    elif shape_type == 'square':
        L = params['L']
        D_eff = L + clearance
        dx = D_eff
        dy = D_eff
    elif shape_type == 'rectangle':
        l, w = params['l'], params['w']
        # Try both orientations
        dx1, dy1 = l + clearance, w + clearance
        dx2, dy2 = w + clearance, l + clearance
        
        # Estimate which orientation fits more shapes
        rows1 = int(sheet_h / dy1)
        cols1 = int(sheet_w / dx1)
        rows2 = int(sheet_h / dy2)
        cols2 = int(sheet_w / dx2)
        
        if rows1 * cols1 >= rows2 * cols2:
            dx, dy = dx1, dy1
        else:
            dx, dy = dx2, dy1
            # Swap l and w for better fit
            params = {'l': w, 'w': l}
    elif shape_type == 'triangle':
        a = params['a']
        h = a * math.sqrt(3) / 2
        dx = a + clearance
        dy = h + clearance
    elif shape_type == 'semi-circle':
        r = params['r']
        dx = 2*r + clearance
        dy = r + clearance
    else:
        raise ValueError(f"Unknown shape type: {shape_type}")

    # Pack shapes sheet by sheet
    while placed < num_shapes:
        sheet_positions = []
        row = 0
        while True:
            # Compute y coordinate for this row
            if shape_type == 'circle':
                y = r + row * dy
                if y > sheet_h - r:
                    break
                x_offset = (dx/2) if (row % 2) else 0
            elif shape_type == 'square':
                y = (L/2) + row * dy
                if y > sheet_h - L/2:
                    break
                x_offset = 0
            elif shape_type == 'rectangle':
                y = (params['w']/2) + row * dy
                if y > sheet_h - params['w']/2:
                    break
                x_offset = 0
            elif shape_type == 'triangle':
                h = a * math.sqrt(3) / 2
                y = h/3 + row * dy
                if y > sheet_h - (2*h/3):
                    break
                x_offset = 0
            elif shape_type == 'semi-circle':
                y = r + row * dy
                if y > sheet_h - r:
                    break
                x_offset = 0

            col = 0
            while True:
                # Compute x coordinate
                if shape_type == 'circle':
                    x = x_offset + r + col * dx
                    bound = sheet_w - r
                elif shape_type == 'square':
                    x = x_offset + L/2 + col * dx
                    bound = sheet_w - L/2
                elif shape_type == 'rectangle':
                    x = x_offset + params['l']/2 + col * dx
                    bound = sheet_w - params['l']/2
                elif shape_type == 'triangle':
                    x = x_offset + a/2 + col * dx
                    bound = sheet_w - a/2
                elif shape_type == 'semi-circle':
                    x = x_offset + r + col * dx
                    bound = sheet_w - r

                if x > bound:
                    break

                if placed < num_shapes:
                    sheet_positions.append({
                        'type': shape_type,
                        'params': params.copy(),
                        'x': x,
                        'y': y
                    })
                    placed += 1
                else:
                    break
                col += 1

            if placed >= num_shapes:
                break
            row += 1

        if not sheet_positions:
            raise RuntimeError(f"Cannot fit any {shape_type}s on one sheet: check dimensions/clearance.")
        sheets.append(sheet_positions)
        
        # If we've placed all shapes, we're done
        if placed >= num_shapes:
            break

    return sheets

def visualize_sheets(sheets: List[List[Dict[str, Any]]], sheet_w: float, sheet_h: float, 
                    clearance_m: float = 0.0, clearance_mm: float = 0.0, 
                    unused_area: float = 0.0, unused_percentage: float = 0.0) -> plt.Figure:
    """
    Draw each sheet side-by-side with its packed shapes.
    Returns a matplotlib figure.
    """
    n_sheets = 1  # Just visualize the first sheet for simplicity
    fig, ax = plt.subplots(figsize=(10, 8))
    margin = 0.5

    # Just use the first sheet for simplicity
    sheet = sheets[0]
    
    # Sheet border
    ax.add_patch(plt.Rectangle((0, 0), sheet_w, sheet_h, fill=False, linewidth=2))

    # Sheet information
    if sheet:
        shape_count = len(sheet)
        shape_type = sheet[0]['type']
        ax.text(sheet_w/2, sheet_h + 0.1, 
                f"{shape_count} {shape_type}s packed", 
                horizontalalignment='center')
        
        # Add unused area information to visualization
        if unused_area > 0:
            ax.text(sheet_w/2, sheet_h + 0.25, 
                    f"Unused area: {unused_area:.3f} m² ({unused_percentage:.1f}%)", 
                    horizontalalignment='center', fontsize=9, color='red')
        
        # Add clearance information if applicable
        if clearance_mm > 0:
            ax.text(sheet_w/2, -0.2, 
                    f"Clearance: {clearance_mm:.1f} mm", 
                    horizontalalignment='center', fontsize=9)

    # Draw shapes with different colors based on type
    color_map = {
        'circle': 'skyblue',
        'square': 'lightgreen',
        'rectangle': 'lightcoral',
        'triangle': 'plum',
        'semi-circle': 'gold'
    }

    for shape in sheet:
        t = shape['type']
        p = shape['params']
        x = shape['x']
        y = shape['y']
        color = color_map.get(t, 'gray')

        if t == 'circle':
            r = p['r']
            ax.add_patch(plt.Circle((x, y), r, edgecolor='black', facecolor=color, alpha=0.8))

        elif t == 'square':
            L = p['L']
            ax.add_patch(plt.Rectangle((x - L/2, y - L/2), L, L,
                                  edgecolor='black', facecolor=color, alpha=0.8))

        elif t == 'rectangle':
            l, w = p['l'], p['w']
            ax.add_patch(plt.Rectangle((x - l/2, y - w/2), l, w,
                                  edgecolor='black', facecolor=color, alpha=0.8))

        elif t == 'triangle':
            a = p['a']
            h = a * math.sqrt(3) / 2
            # an upward equilateral triangle centered at (x,y):
            pts = [
                (x,         y + 2*h/3),
                (x - a/2,   y - h/3),
                (x + a/2,   y - h/3)
            ]
            ax.add_patch(plt.Polygon(pts, edgecolor='black', facecolor=color, alpha=0.8))

        elif t == 'semi-circle':
            r = p['r']
            # semicircle flat side down with center at (x,y)
            # Using patches.Wedge instead of plt.Wedge
            ax.add_patch(patches.Wedge((x, y), r, 0, 180,
                              edgecolor='black', facecolor=color, alpha=0.8))

    ax.set_xlim(-0.5, sheet_w + 0.5)
    ax.set_ylim(-0.5, sheet_h + 0.5)
    ax.set_aspect('equal')
    
    # Add grid lines for reference
    ax.grid(True, linestyle='--', alpha=0.3)
    
    # Add axes labels
    ax.set_xlabel('Width (meters)')
    ax.set_ylabel('Height (meters)')
    
    # Add title
    ax.set_title("Sheet Layout (dimensions in meters)")
    
    plt.tight_layout()
    return fig

def calculate_shape_area(shape_type: str, params: Dict[str, float]) -> float:
    """Calculate the area of a shape based on its type and parameters."""
    if shape_type == 'circle':
        r = params['r']
        return math.pi * r * r
    elif shape_type == 'square':
        L = params['L']
        return L * L
    elif shape_type == 'rectangle':
        l, w = params['l'], params['w']
        return l * w
    elif shape_type == 'triangle':
        a = params['a']
        h = a * math.sqrt(3) / 2
        return (a * h) / 2
    elif shape_type == 'semi-circle':
        r = params['r']
        return (math.pi * r * r) / 2
    else:
        raise ValueError(f"Unknown shape type: {shape_type}")

def calculate_unused_area(shape_type: str, shape_params: Dict[str, float], 
                         sheet_w: float, sheet_h: float, count: int) -> float:
    """Calculate the unused area on the sheet after packing shapes."""
    sheet_area = sheet_w * sheet_h
    shape_area = calculate_shape_area(shape_type, shape_params)
    total_shape_area = shape_area * count
    return sheet_area - total_shape_area

# Main Streamlit UI
with st.sidebar:
    st.header("Sheet Parameters")
    sheet_w = st.number_input("Sheet Width (meters)", min_value=0.01, value=1.0, step=0.1, format="%.2f")
    sheet_h = st.number_input("Sheet Height (meters)", min_value=0.01, value=1.0, step=0.1, format="%.2f")
    clearance = st.number_input("Clearance Between Shapes (mm)", min_value=0.0, value=5.0, step=0.5, format="%.1f")
    
    st.header("Shape Selection")
    shape_type = st.selectbox(
        "Select Shape to Pack",
        options=["circle", "square", "rectangle", "triangle", "semi-circle"],
        format_func=lambda x: x.capitalize()
    )
    
    # Dynamic shape parameters based on selection
    st.subheader("Shape Parameters")
    
    shape_params = {}
    if shape_type == "circle":
        r = st.number_input("Circle Radius (meters)", min_value=0.01, value=0.1, step=0.01, format="%.2f")
        shape_params["r"] = r
    elif shape_type == "square":
        L = st.number_input("Square Side Length (meters)", min_value=0.01, value=0.1, step=0.01, format="%.2f")
        shape_params["L"] = L
    elif shape_type == "rectangle":
        l = st.number_input("Rectangle Length (meters)", min_value=0.01, value=0.2, step=0.01, format="%.2f")
        w = st.number_input("Rectangle Width (meters)", min_value=0.01, value=0.1, step=0.01, format="%.2f")
        shape_params["l"] = l
        shape_params["w"] = w
    elif shape_type == "triangle":
        a = st.number_input("Triangle Side Length (meters)", min_value=0.01, value=0.1, step=0.01, format="%.2f")
        shape_params["a"] = a
    elif shape_type == "semi-circle":
        r = st.number_input("Semi-Circle Radius (meters)", min_value=0.01, value=0.1, step=0.01, format="%.2f")
        shape_params["r"] = r
    
    calculate_button = st.button("Calculate Packing", type="primary")

# Main content area
if calculate_button:
    with st.spinner("Calculating packing arrangement..."):
        try:
            # Convert clearance from mm to meters
            clearance_m = clearance / 1000.0
            
            # Calculate sheet area and shape area
            sheet_area = sheet_w * sheet_h
            shape_area = calculate_shape_area(shape_type, shape_params)
            
            # Theoretical upper bound based on area
            area_bound = int(sheet_area // shape_area)
            
            # Pack shapes
            sheets = pack_shapes(shape_type, shape_params, area_bound, sheet_w, sheet_h, clearance_m)
            
            # Get results
            count_on_sheet = len(sheets[0])
            total_sheets = len(sheets)
            total_shapes = sum(len(sheet) for sheet in sheets)
            efficiency = (count_on_sheet / area_bound) * 100
            
            # Calculate unused area
            unused_area = calculate_unused_area(shape_type, shape_params, sheet_w, sheet_h, count_on_sheet)
            unused_percentage = (unused_area / (sheet_w * sheet_h)) * 100
            
            # Display results
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.subheader("Results")
                st.metric("Shapes per Sheet", count_on_sheet)
                st.metric("Theoretical Maximum", area_bound)
                st.metric("Packing Efficiency", f"{efficiency:.1f}%")
                
                # Display unused area information
                st.subheader("Unused Area")
                st.metric("Unused Area", f"{unused_area:.3f} m²")
                st.metric("Percentage Unused", f"{unused_percentage:.1f}%")
                
                # Show shape parameters
                st.subheader("Shape Parameters")
                param_text = ""
                if shape_type == "circle":
                    param_text = f"Radius: {shape_params['r']} meters"
                elif shape_type == "square":
                    param_text = f"Side Length: {shape_params['L']} meters"
                elif shape_type == "rectangle":
                    param_text = f"Length: {shape_params['l']} meters, Width: {shape_params['w']} meters"
                elif shape_type == "triangle":
                    param_text = f"Side Length: {shape_params['a']} meters"
                elif shape_type == "semi-circle":
                    param_text = f"Radius: {shape_params['r']} meters"
                st.text(param_text)
                
                # Additional details
                st.text(f"Sheet size: {sheet_w}m × {sheet_h}m")
                st.text(f"Clearance: {clearance} mm")
            
            with col2:
                st.subheader("Visualization")
                fig = visualize_sheets(sheets, sheet_w, sheet_h, clearance_m, clearance, 
                                  unused_area, unused_percentage)
                st.pyplot(fig)
            
        except Exception as e:
            st.error(f"Error: {str(e)}")
            
else:
    # Display instructions when first loading the page
    st.markdown("""
    ## Instructions
    
    1. Set the sheet dimensions (width and height) in meters
    2. Enter the clearance between shapes in millimeters
    3. Select the shape type from the dropdown
    4. Enter the shape dimensions
    5. Click "Calculate Packing" to see results
    
    The application will show:
    - How many shapes can fit on a sheet
    - The theoretical maximum based on area
    - A visualization of the packed shapes
    - Unused area calculation and visualization
    
    ## About
    
    This application calculates the optimal packing of shapes onto a rectangular sheet.
    It supports various shapes including circles, squares, rectangles, triangles, and semi-circles.
    The algorithm attempts to place shapes efficiently while maintaining the specified clearance between them.
    """)

# Footer
st.markdown("---")
st.markdown("Nesting Calculator - A Streamlit Application")
