import plotly.io as pio
import plotly.graph_objects as go

# Define the custom color palette
custom_colors = {
    'blue': '#1f77b4',
    'orange': '#ff7f0e',
    'green': '#2ca02c',
    'red': '#d62728',
    'purple': '#9467bd',
    'brown': '#8c564b',
    'pink': '#e377c2',
    'gray': '#7f7f7f',
    'turquoise': '#17becf',
    'yellow': '#bcbd22'
}

# Create the template object
custom_template = go.layout.Template(
    layout=go.Layout(
        # Define the default color sequence for discrete data
        colorway=list(custom_colors.values()),
        
        # Set background colors
        paper_bgcolor='#eff5f5',  # Main background
        plot_bgcolor='#eff5f5',   # Plotting area background
        
        # Define fonts for consistency
        font=dict(
            family="Roboto Condensed, sans-serif",
            size=12,
            color= '#122c4f'
        ),
        
        # Customize titles
        title=dict(
            font_size=20,
            x=0.05, # Align title to the left
            xanchor='left'
        ),
        
        # Customize grid lines for a cleaner look
        xaxis=dict(gridcolor='#dddddd'),
        yaxis=dict(gridcolor='#dddddd')
    )
)

# Register the custom template with Plotly
pio.templates['custom_template'] = custom_template