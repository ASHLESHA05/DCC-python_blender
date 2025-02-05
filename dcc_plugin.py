import bpy
import requests  # To send data to the server
import os

class DCC_transform(bpy.types.Panel):
    bl_label = "DCC  Plugin"
    bl_idname = "DCC_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'DCC Plugin'

    def draw(self, context):
        layout = self.layout
        obj = context.object

        if obj:
            # Display object transforms
            layout.label(text=f"Selected: {obj.name}")
            layout.prop(obj, "location")
            layout.prop(obj, "rotation_euler")
            layout.prop(obj, "scale")

            # Dropdown for API endpoints
            layout.prop(context.scene, "api_endpoint")

            # Submit button
            layout.operator("dcc.send_transform")
        else:
            layout.label(text="No object selected")

class DCC_send(bpy.types.Operator):
    bl_label = "Send Transform"
    bl_idname = "dcc.send_transform"

    def execute(self, context):
        obj = context.object
        if obj:
            data = {}
            
            data = {
                "position": list(obj.location),
                "rotation": list(obj.rotation_euler),
                "scale": list(obj.scale),
            }
            endpoint = context.scene.api_endpoint

            if endpoint == 'translation':
                data ={
                    'position': list(obj.location)
                }
            elif endpoint == 'rotation':
                data ={
                    'rotation' : list(obj.rotation_euler)
                }
            elif endpoint == 'scale':
                data = {
                    'scale':list(obj.scale)
                }
            FLASK_URL = os.getenv("FLASK_URL", "http://localhost")  # Default to localhost
            PORT = os.getenv("PORT", "5000")  # Default to port 5000

            url = f"{FLASK_URL}:{PORT}/{endpoint}"  

            try:
                response = requests.post(url, json=data)
                self.report({'INFO'}, f"Sent data: {response.status_code}")
            except Exception as e:
                self.report({'ERROR'}, f"Failed: {e}")

        return {'FINISHED'}

def register():
    bpy.utils.register_class(DCC_transform)
    bpy.utils.register_class(DCC_send)
    bpy.types.Scene.api_endpoint = bpy.props.EnumProperty(
        name="API Endpoint",
        items=[
            ('transform', "All Transforms", ""),
            ('translation', "Position Only", ""),
            ('rotation', "Rotation Only", ""),
            ('scale', "Scale Only", ""),
        ]
    )

def unregister():
    bpy.utils.unregister_class(DCC_transform)
    bpy.utils.unregister_class(DCC_send)
    del bpy.types.Scene.api_endpoint

if __name__ == "__main__":
    register()
