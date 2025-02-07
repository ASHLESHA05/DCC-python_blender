import bpy
import requests
import os
from math import radians

class DCC_transform(bpy.types.Panel):
    bl_label = "DCC Plugin"
    bl_idname = "DCC_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'DCC Plugin'

    def draw(self, context):
        layout = self.layout
        obj = context.object

        # Add button to fetch and create items
        layout.operator("dcc.fetch_items", text="Fetch Items from Database")

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

class DCC_fetch_items(bpy.types.Operator):
    bl_label = "Fetch Items"
    bl_idname = "dcc.fetch_items"

    def create_cube_for_item(self, name, quantity):
        # Create a cube
        bpy.ops.mesh.primitive_cube_add(size=1.0)
        cube = bpy.context.active_object
        
        # Name the cube based on item name and quantity
        cube.name = f"{name}_{quantity}"
        
        # Set default transforms
        cube.location = (0, 0, 0)
        cube.rotation_euler = (0, 0, 0)
        cube.scale = (1, 1, 1)
        
        # Add custom properties to store item info
        cube["item_name"] = name
        cube["quantity"] = quantity

    def execute(self, context):
        FLASK_URL = os.getenv("FLASK_URL", "http://localhost")
        PORT = os.getenv("PORT", "5000")
        
        url = f"{FLASK_URL}:{PORT}/get-all-items"
        
        try:
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()['res']
                
                # Create a collection for our items if it doesn't exist
                collection_name = "Database_Items"
                if collection_name not in bpy.data.collections:
                    new_collection = bpy.data.collections.new(collection_name)
                    bpy.context.scene.collection.children.link(new_collection)
                
                # Set the active collection
                collection = bpy.data.collections[collection_name]
                
                # Clear existing objects in the collection
                for obj in collection.objects:
                    bpy.data.objects.remove(obj, do_unlink=True)
                
                # Create cubes for each item
                spacing = 2.0  
                for i, item in enumerate(data):
                    name = item[1]  # item name
                    quantity = item[2]  # item quantity
                    
                    # Create a cube
                    bpy.ops.mesh.primitive_cube_add(size=1.0)
                    cube = bpy.context.active_object
                    
                    # Move from default collection to our collection
                    bpy.context.scene.collection.objects.unlink(cube)
                    collection.objects.link(cube)
                    
                    # Name and position the cube
                    cube.name = f"{name}_{quantity}"
                    cube.location = (i * spacing, 0, 0)  
                    
                    # Add custom properties
                    cube["item_name"] = name
                    cube["quantity"] = quantity
                
                self.report({'INFO'}, f"Created {len(data)} items from database")
                
            else:
                self.report({'ERROR'}, f"Failed to fetch items: {response.status_code}")
                
        except Exception as e:
            self.report({'ERROR'}, f"Error: {str(e)}")
            
        return {'FINISHED'}

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
                data = {
                    'position': list(obj.location)
                }
            elif endpoint == 'rotation':
                data = {
                    'rotation': list(obj.rotation_euler)
                }
            elif endpoint == 'scale':
                data = {
                    'scale': list(obj.scale)
                }
            
            # Add item information to the data if it exists
            if "item_name" in obj:
                data["item_name"] = obj["item_name"]
                data["quantity"] = obj["quantity"]

            FLASK_URL = os.getenv("FLASK_URL", "http://localhost")
            PORT = os.getenv("PORT", "5000")

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
    bpy.utils.register_class(DCC_fetch_items)
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
    bpy.utils.unregister_class(DCC_fetch_items)
    del bpy.types.Scene.api_endpoint

if __name__ == "__main__":
    register()