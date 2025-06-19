#version 330

uniform vec3 fadeCenter;
uniform float fadeDistance;
uniform vec4 fadeColor;
in vec3 worldPos;

out vec4 fragColor;

void main(){
    float distance=length(worldPos.xy-fadeCenter.xy);// Use 2D distance for grid fading
    float alpha=clamp(1.-(distance/fadeDistance),0.,1.);
    fragColor=vec4(fadeColor.rgb,fadeColor.a*alpha);
}
