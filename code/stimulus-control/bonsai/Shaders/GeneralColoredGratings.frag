#version 400

uniform sampler2D baseTexture;  // Input texture
uniform float applyBlueOnly = 1.0;     // Toggle for blue-only effect

in vec2 texCoord;
out vec4 fragColor;

void main()
{
    vec4 baseColor = texture(baseTexture, texCoord);

    if (applyBlueOnly == 1.0) {
        // Zero out the red and green channels
        baseColor.r = 0.0;
        baseColor.g = 0.0;
    }

    // Output the final color
    fragColor = baseColor;
}