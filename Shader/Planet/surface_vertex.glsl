#version 150

#include "Includes/Configuration.include"
#include "Includes/VertexOutput.include"

// Matrices
uniform mat4 trans_model_to_world;

// Material properties
in vec4 p3d_Vertex;
in vec3 p3d_Normal;
in vec3 p3d_Tangent;
in vec3 p3d_Binormal;

in vec2 p3d_MultiTexCoord0;

// Outputs
out VertexOutput vOutput;

// We get the material info from panda as a struct
struct PandaMaterial {
    vec4 diffuse;
    vec3 specular;
    vec4 ambient;
};
uniform PandaMaterial p3d_Material;

uniform mat4 p3d_ModelViewProjectionMatrix;

// We need this for the velocity
uniform mat4 lastMVP;

void main() {
    // Start sphereization code
    // Replace p3d_Vertex with our own variable for planet transformations
    vec4 v = p3d_Vertex;
    //By adding 1 to z we move our grid to make a cube.
    //We do 1 instead of 0.5 to make all the math easy - set radius not diameter
    v.z += 1.0;
    //vec4 vertex = v;//Shows it as a cube
    // Normalize! Use vertex instead of p3dvertex
    vec4 vertex = vec4(normalize(v.xyz), v.w);
    vec3 normal = vertex.xyz; // Works only for sphere

    //double iy = 1/sqrt(normal.x*normal.x+normal.z*normal.z);
    //vec x (-normal.z*iy,0,normal.x*iy);

    vec3 tangent = p3d_Tangent;

    vec3 c1 = cross(normal, vec3(0.0, 0.0, 1.0));
	vec3 c2 = cross(normal, vec3(0.0, 1.0, 0.0));

	if(length(c1)>length(c2))
	{
		tangent = c1;
	}
	else
	{
		tangent = c2;
	}

	tangent = normalize(tangent);


    //vec3 tangent = normalize(p3d_Tangent - normal);
    vec3 binormal = cross(tangent, normal);

    //tangent = p3d_Tangent;
    //binormal = p3d_Binormal;
    //End spherization code

    // Start RenderPipeline code
    // Transform normal to world space
    vOutput.normalWorld   = normalize(trans_model_to_world * vec4(normal, 0) ).xyz;
    vOutput.tangentWorld  = normalize(trans_model_to_world * vec4(tangent, 0) ).xyz;
    vOutput.binormalWorld = normalize(trans_model_to_world * vec4(binormal, 0) ).xyz;

    vOutput.tangentWorld = tangent;
    vOutput.binormalWorld = binormal;
    vOutput.normalWorld = normal;


    // vOutput.normalWorld = FAST_mul_no_w(trans_model_to_world, p3d_Normal).rgb;

    // Transform position to world space
    vOutput.positionWorld = (trans_model_to_world * vertex).xyz;
    // vOutput.positionWorld = FAST_mul(trans_model_to_world, p3d_Vertex).xyz;

    // Pass texcoord to fragment shader
    vOutput.texcoord = p3d_MultiTexCoord0.xy;

    // Also pass diffuse to fragment shader
    vOutput.materialDiffuse = p3d_Material.diffuse;
    vOutput.materialSpecular = p3d_Material.specular;
    vOutput.materialAmbient = p3d_Material.ambient.z;

    // Compute velocity in vertex shader, but it's important
    // to move the w-divide to the fragment shader
    // vOutput.lastProjectedPos = lastMVP * vec4(vOutput.positionWorld, 1) * vec4(1,1,1,2);
    vOutput.lastProjectedPos = FAST_mul(lastMVP, vOutput.positionWorld) * vec4(1,1,1,2);

    // Transform vertex to window space
    // Only required when not using tesselation shaders
    gl_Position = p3d_ModelViewProjectionMatrix * vertex;
    // gl_Position = FAST_mul(p3d_ModelViewProjectionMatrix, p3d_Vertex);
}

