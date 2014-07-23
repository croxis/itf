#version 150

#include "Includes/VertexOutput.include"

layout(triangles) in;
layout(triangle_strip, max_vertices=3) out;

in VertexOutput vOut[3];

out VertexOutput vOutput;

 void main()
{
  for(int i = 0; i < gl_in.length(); i++)
  {
     // copy attributes
    gl_Position = gl_in[i].gl_Position;
    vOutput.positionWorld = vOut[i].positionWorld;
    vOutput.normalWorld = vOut[i].normalWorld;
    vOutput.texcoord = vOut[i].texcoord;

    vOutput.materialDiffuse = vOut[i].materialDiffuse;
    vOutput.materialSpecular = vOut[i].materialSpecular;
    vOutput.materialAmbient = vOut[i].materialAmbient;

    vOutput.tangentWorld = vOut[i].tangentWorld;
    vOutput.binormalWorld = vOut[i].binormalWorld;

    vOutput.lastProjectedPos = vOut[i].lastProjectedPos;

    // done with the vertex
    EmitVertex();
  }
  EndPrimitive();
}