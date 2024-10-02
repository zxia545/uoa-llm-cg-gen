import numpy as np
import plotly.graph_objects as go
import time

# Plane equation: 3x + 2y - z = 3
# Normal to the plane: [3, 2, -1]
# Ray with c = 3/2: p(t) = [1, 0, 1] + t * [-1, 3/2, 0]

# Create a meshgrid for the plane
xx, yy = np.meshgrid(range(-5, 6), range(-5, 6))
zz = 3 * xx + 2 * yy - 3

# Parameters for the ray
c = 3/2
t_values = np.linspace(-5, 5, 200)
ray_x = 1 + t_values * -1
ray_y = 0 + t_values * c
ray_z = 1 + t_values * 0

# Create the Plotly figure
fig = go.Figure()

# Add the plane
fig.add_trace(go.Surface(x=xx, y=yy, z=zz, opacity=0.5, colorscale='Viridis', name="Plane"))

# Add the ray
fig.add_trace(go.Scatter3d(x=ray_x, y=ray_y, z=ray_z, mode='lines', name='Ray', line=dict(color='red', width=5)))

# Set the plot layout
fig.update_layout(scene=dict(
    xaxis_title='X',
    yaxis_title='Y',
    zaxis_title='Z'),
    title='Visualization of a Plane and a Parallel Ray')

# Save the figure to an HTML file
fig.write_html(f'temp_{time.time()}.html')