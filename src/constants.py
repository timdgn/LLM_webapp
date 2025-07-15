import os


PROJECT_DIR = os.path.dirname(os.path.dirname(__file__))
THREADS_DIR = os.path.join(PROJECT_DIR, "data", "thread_history")
UPLOADED_IMAGES_DIR = os.path.join(PROJECT_DIR, "data", "uploaded_images")
GENERATED_IMAGES_DIR = os.path.join(PROJECT_DIR, "data", "generated_images")
INPAINTING_IMAGES_DIR = os.path.join(PROJECT_DIR, "data", "inpainting_images")

MODEL = "gpt-4.1-mini"

INTERACTION_TYPES = {'chat': 'ChatGPT',
                     'image': 'DALL-E (Image Generation)',
                     'inpainting': 'DALL-E (Inpainting) - Beta ⚠️'}

AVATARS = {"user": "🧑‍⚕️", "assistant": "🤖"}

CATEGORIES = ["album cover", "anatomical drawing", "anatomy", "animal", "anime character design", "art", "book cover", "botanical watercolor", "brand identity", 
              "business card", "calendar design", "character design", "character design multiple poses", "character sheet", "chart design", "coloring book page",
              "coloring pages", "comic strips", "color palette", "cute animals", "doll house", "enamel pin", "encyclopedia page", "fashion moodboard", 
              "flat lay photography", "flyer", "full body character design", "game assets", "game ui", "house cutaway", "house plan", "icon set design", 
              "ikea guide", "illustration split circle four seasons", "illustrations", "infographic", "interior design", "jewelry design", "knolling",
              "logo design", "magazine cover", "menu design", "mobile app ui design", "nail art", "newsletter design", "nursery", "outfit", "packaging design",
              "popup book", "postage stamp", "poster", "propaganda poster", "reference sheet", "schematic diagram", "seamless pattern", "sticker", "story board",
              "tarot card", "tattoo design", "tshirt", "t shirt vector", "wall painting", "watercolor", "watercolor animals", "website design", "wedding invitation"]

STYLES = ["3D", "Abstract Art", "Abstract Expressionism", "Abstract Illusion", "Action Painting", "Alebrijes", "Analytical Cubism", "Art Brut", "Art Deco", 
          "Art Nouveau", "Arte Povera", "Automatism", "Bauhaus", "Bayeux Tapestry", "Britpop", "Bronze Age", "Brutalism", "Bubble Goth", "Caricature",
          "Cartographic Art", "Cartoon", "Childrens Book Illustration", "Cinematic", "Cloisonnism", "Collage Art", "Color Field Painting", "Colorful Collages", 
          "Commercial Art", "Comic", "Conceptual Art", "Concretism", "Constructivism", "Coptic Art", "Cubism", "Expressionism", "Impressionism", "Realism", "Surrealism"]

LIGHTING = ["Backlighting", "Blacklight", "Blue Hour", "Bokeh", "Chemiluminescence", "Cinematic Lighting", "Crepuscular Rays", "Dappled Light", "Disco Lighting",
            "Dramatic Lighting", "Dreamy Glow", "Dual Lighting", "Dusk", "Electroluminescent Wire", "Electromagnetic Spectrum", "Flare", "Floodlight",
            "Flourescent Lightin", "Frontal Lighting", "Glitter", "Glow In The Dark", "Glowing", "Glowing Neon", "Glowing Partical Effects", "Glowing Radioactively",
            "Gobo", "Golden Hour", "Hard Lighting", "High Key Lighting", "Internal Glow", "Laser", "Lava Glow", "Lens Flare", "Low Key Lighting", "Midnight",
            "Moody Lighting", "Moonlight", "Neon Lights", "Nightclub Lighting", "Nuclear Wasted Glow", "Prismatic Highlights", "Radioluminescence", "Rainbow Sparks",
            "Ray Tracing Reflections", "Shimmering Lights", "Soft Lighting", "Starry", "Sunlighting", "Sunlit", "Torchlit", "Twilight Hour"]

CAMERA_ANGLES = ["100mm", "14mm", "16k", "24mm", "300mm", "32k", "35mm", "360-degree camera", "400mm", "4k", "500mm", "600mm", "85mm", "8k", "Abstract perspective",
                 "Aerial Photography", "Black and white", "Bokeh effect", "Circular fisheye lens", "Closeup", "Double exposure", "Drone Photography", "Dutch angle",
                 "Experimental photography", "Far Shot", "Film noir style", "Focal Blur", "Full Body Shot", "Full Focus", "Ghostly blur", "Glitch art", "Headshot Photography",
                 "High Angle Shot", "High contrast", "Holga camera", "Infrared photography", "Lenticular lens", "Light painting", "Long Exposure", "Low Angle Shot",
                 "Macro Lens", "Medium Shot", "Minimalist style", "Motion blur", "Neon lighting", "Night vision", "Oblique angle", "Out Of Focus", "Panoramic view",
                 "Pixelated effect", "Polaroid camera", "Portrait Photography", "Prism lens", "Refraction effect", "Retro style", "Selfie", "Short Exposure",
                 "Split focus", "Stereoscopic 3D", "Telephoto Lens", "Tiltshift", "Time-lapse", "Top Down Shot", "Ultra Wide Angle", "Underwater photography",
                 "Vintage look", "Wide Angle"]

COLORS = ["AliceBlue", "AntiqueWhite", "Aqua", "Aquamarine", "Azure", "Beige", "Bisque", "Black", "BlanchedAlmond", "Blue", "BlueViolet", "Brown", "BurlyWood",
          "CadetBlue", "Chartreuse", "Chocolate", "Coral", "CornflowerBlue", "Cornsilk", "Crimson", "Cyan", "DarkBlue", "DarkCyan", "DarkGoldenRod", "DarkGray",
          "DarkGreen", "DarkGrey", "DarkKhaki", "DarkMagenta", "DarkOliveGreen", "DarkOrange", "DarkOrchid", "DarkRed", "DarkSalmon", "DarkSeaGreen", "DarkSlateBlue",
          "DarkSlateGray", "DarkSlateGrey", "DarkTurquoise", "DarkViolet", "DeepPink", "DeepSkyBlue", "DimGray", "DimGrey", "DodgerBlue", "FireBrick", "FloralWhite",
          "ForestGreen", "Fuchsia", "Gainsboro", "Green", "Orange", "Red", "White", "Yellow"]

TEXTURES = ["3d fractals", "agate", "aluminum", "amber", "amethyst", "amigurumi", "ammolite", "anodized", "anodized titanium", "awning stripe", "basalt",
            "brass", "breton stripes pattern", "brick", "bronze", "brushed aluminum", "bumpy", "candy stripes", "celtic knot", "ceramic", "chain pattern", "chainmail",
            "chalk stripes"]

SYSTEM_PROMPTS = {
    "Default": "",
    "Data Scientist": """<SYSTEM PROMPT>
        You are an expert in Python development, including its core libraries, popular frameworks like Flask, Streamlit and FastAPI, data science libraries such as NumPy and Pandas, and testing frameworks like pytest. You excel at selecting the best tools for each task, always striving to minimize unnecessary complexity and code duplication.
        When making suggestions, you break them down into discrete steps, recommending small tests after each stage to ensure progress is on the right track.
        You provide code examples when illustrating concepts or when specifically asked. However, if you can answer without code, that is preferred. You're open to elaborating if requested.
        Before writing or suggesting code, you conduct a thorough review of the existing codebase, describing its functionality between <CODE_REVIEW> tags. After the review, you create a detailed plan for the proposed changes, enclosing it in <PLANNING> tags. You pay close attention to variable names and string literals, ensuring they remain consistent unless changes are necessary or requested. When naming something by convention, you surround it with double colons and use ::UPPERCASE::.
        Your outputs strike a balance between solving the immediate problem and maintaining flexibility for future use.
        You always seek clarification if anything is unclear or ambiguous. You pause to discuss trade-offs and implementation options when choices arise.
        It's crucial that you adhere to this approach, teaching your conversation partner about making effective decisions in Python development. You avoid unnecessary apologies and learn from previous interactions to prevent repeating mistakes.
        You are highly conscious of security concerns, ensuring that every step avoids compromising data or introducing vulnerabilities. Whenever there's a potential security risk (e.g., input handling, authentication management), you perform an additional review, presenting your reasoning between <SECURITY_REVIEW> tags.
        Lastly, you consider the operational aspects of your solutions. You think about how to deploy, manage, monitor, and maintain Python applications. You highlight relevant operational concerns at each step of the development process. Answer in the language of the following user prompt.
        <END OF SYSTEM PROMPT>""",
    "Image Generator": f"""<SYSTEM PROMPT>
        DALLE-3 is an AI art generation model.
        Below are lists of words describing different aspects of an image, that can be used to generate images with DALLE-3:
        CATEGORIES: {CATEGORIES}
        STYLES: {STYLES}
        LIGHTING: {LIGHTING}
        CAMERA_ANGLES: {CAMERA_ANGLES}
        COLORS: {COLORS}
        TEXTURES: {TEXTURES}
        I want you to write me 5 detailed prompts using several of the above categories. Use as many words from the lists as you find relevant. In the prompt, describe the scene, and follow by adding only relevant modifiers words from the lists that are relevant to the user's scene description and can enhance the image, divided by commas, to alter the mood, style, lighting, and more.
        Here is the idea you have to work on:
        </END OF SYSTEM PROMPT>"""}