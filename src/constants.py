import os


PROJECT_DIR = os.path.dirname(os.path.dirname(__file__))
THREADS_DIR = os.path.join(PROJECT_DIR, "data", "thread_history")
UPLOADED_IMAGES_DIR = os.path.join(PROJECT_DIR, "data", "uploaded_images")
GENERATED_IMAGES_DIR = os.path.join(PROJECT_DIR, "data", "generated_images")

INTERACTION_TYPES = {'chat': 'ChatGPT',
                     'image': 'DALL-E (Image Generation)'}

AVATARS = {"user": "🧑‍⚕️", "assistant": "🤖"}

CATEGORIES = ["album cover", "anatomical drawing", "anatomy", "book cover", "business card", "brand identity", "calendar design", "character design",
              "character design multiple poses", "character sheet", "chart design", "doll house", "color palette", "enamel pin", "comic strips", "coloring book page",
              "encyclopedia page", "fashion moodboard", "flat lay photography", "flyer", "full body character design", "game assets", "game ui", "house cutaway",
              "house plan", "icon set design", "ikea guide", "illustration split circle four seasons", "infographic", "interior design", "jewelry design", "knolling",
              "logo design", "magazine cover", "menu design", "mobile app ui design", "packaging design", "outfit", "newsletter design", "nail art", "popup book",
              "postage stamp", "poster", "propaganda poster", "sticker", "seamless pattern", "schematic diagram", "reference sheet", "story board", "wall painting",
              "wedding invitation", "t shirt vector", "tarot card", "tattoo design", "anime character design", "website design", "illustrations", "coloring pages",
              "watercolor", "watercolor animals", "nursery", "tshirt", "cute animals", "art", "animal", "botanical watercolor"]

STYLES = ["3D", "Abstract Art", "Abstract Expressionism", "Analytical Cubism", "Art Brut", "Art Deco", "Art Nouveau", "Bayeux Tapestry", "Britpop", "Bronze Age",
          "Cartographic Art", "Cartoon", "Childrens Book Illustration", "Color Field Painting", "Colorful Collages", "Comic", "Constructivism", "Coptic Art", "Cubism",
          "Impressionism", "Abstract Illusion", "Action Painting", "Alebrijes", "Arte Povera", "Automatism", "Bauhaus", "Brutalism", "Bubble Goth", "Caricature",
          "Cinematic", "Cloisonnism", "Collage Art", "Commercial Art", "Conceptual Art", "Concretism", "Surrealism", "Realism", "Expressionism"]

LIGHTING = ["Backlighting", "Blacklight", "Blue Hour", "Bokeh", "Chemiluminescence", "Cinematic Lighting", "Crepuscular Rays", "Dappled Light", "Disco Lighting",
            "Dramatic Lighting", "Dreamy Glow", "Dual Lighting", "Dusk", "Electroluminescent Wire", "Electromagnetic Spectrum", "Flare", "Floodlight",
            "Flourescent Lightin", "Frontal Lighting", "Glitter", "Glow In The Dark", "Glowing", "Glowing Neon", "Glowing Partical Effects", "Glowing Radioactively",
            "Gobo", "Golden Hour", "Hard Lighting", "High Key Lighting", "Internal Glow", "Laser", "Lava Glow", "Lens Flare", "Low Key Lighting", "Midnight",
            "Moody Lighting", "Moonlight", "Neon Lights", "Nightclub Lighting", "Nuclear Wasted Glow", "Prismatic Highlights", "Radioluminescence", "Rainbow Sparks",
            "Ray Tracing Reflections", "Shimmering Lights", "Soft Lighting", "Starry", "Sunlighting", "Sunlit", "Torchlit", "Twilight Hour"]

ARTISTS = ["Adrian Donoghue", "Adrian Tomine", "Akihiko Yoshida", "Akira Toriyama", "Akos Major", "Alan Lee", "Albert Watson", "Alberto Seveso", "Alex Grey",
           "Alex Timmermans", "Alphonse Mucha", "Andro Botticelli", "Anna Dittmann", "Anne Bachelier", "Antonio Mora", "Arshile Gorky", "Arthur Rackham",
           "Atey Ghailan", "Aubrey Beardsley", "August Macke", "Basquiat", "Benoit Mandelbrot", "Bernie Fuchs", "Bernini", "Bill Mantlo", "Bob Eggleton", "Brian Bolland",
           "Brian Froud", "Brian Kesinger", "Brothers Hildebrandt", "Bruce Pennington", "Butcher Billy", "Cai Guo Qiang", "Canaletto", "Caravaggio", "Charlie Bowater",
           "Chiharu Shiota", "Cindy Sherman", "Claude Monet", "Coby Whitmore", "Conrad Roset", "Craig Mullins", "Daido Moriyama", "Dante Gabriel Rossetti", "David Hockney",
           "Diego Rivera", "Donatello", "Dorothy Lathrop", "Drew Struzan", "El Anatsui", "El Lissitzky", "Ellen Jewett", "Enki Bilal", "Erte", "Escher", "Francisco De Goya",
           "Francoise Nielly", "Frank Miller", "Frank Thorne", "Frida Kahlo", "Fullmetal Alchemist", "Georg Baselitz", "Georges De La Tou", "Picasso", "Van Gogh", "Da Vinci",
           "Michelangelo", "Rembrandt"]

CAMERA_ANGLES = ["360-degree camera", "100mm", "14mm", "16k", "24mm", "300mm", "32k", "35mm", "400mm", "4k", "500mm", "600mm", "85mm", "8k", "High contrast",
                 "Holga camera", "Infrared photography", "Lenticular lens", "Light painting", "Minimalist style", "Motion blur", "Neon lighting", "Night vision",
                 "Oblique angle", "Panoramic view", "Pixelated effect", "Polaroid camera", "Prism lens", "Refraction effect", "Retro style", "Split focus",
                 "Stereoscopic 3D", "Time-lapse", "Underwater photography", "Vintage look", "Abstract perspective", "Black and white", "Bokeh effect", "Circular fisheye lens",
                 "Double exposure", "Dutch angle", "Experimental photography", "Film noir style", "Ghostly blur", "Glitch art", "Aerial Photography", "Closeup",
                 "Drone Photography", "Far Shot", "Focal Blur", "Full Body Shot", "Full Focus", "Headshot Photography", "High Angle Shot", "Long Exposure", "Low Angle Shot",
                 "Macro Lens", "Medium Shot", "Out Of Focus", "Portrait Photography", "Selfie", "Short Exposure", "Telephoto Lens", "Tiltshift", "Top Down Shot",
                 "Ultra Wide Angle", "Wide Angle"]

COLORS = ["Red", "Blue", "Green", "Yellow", "Orange", "AliceBlue", "AntiqueWhite", "Aqua", "Aquamarine", "Azure", "Beige", "Bisque", "Black", "BlanchedAlmond",
          "Blue", "BlueViolet", "Brown", "BurlyWood", "CadetBlue", "Chartreuse", "Chocolate", "Coral", "CornflowerBlue", "DarkBlue", "DarkCyan", "DarkGoldenRod",
          "DarkGray", "DarkGrey", "DarkMagenta", "DarkOliveGreen", "DarkOrange", "DarkOrchid", "DarkSeaGreen", "DarkSlateBlue", "DarkSlateGray", "DarkSlateGrey",
          "DeepPink", "DeepSkyBlue", "DimGray", "DimGrey", "DodgerBlue", "ForestGreen", "Fuchsia", "Gainsboro", "Cornsilk", "Crimson", "Cyan", "DarkGreen", "DarkKhaki",
          "DarkRed", "DarkSalmon", "DarkTurquoise", "DarkViolet", "FireBrick", "FloralWhite"]


TEXTURES = ["3d fractals", "anodized titanium", "brushed aluminum", "agate", "aluminum", "awning stripe", "ceramic", "amber", "basalt", "celtic knot", "anodized", "brass",
            "bumpy", "chalk stripes", "ammolite", "breton stripes pattern", "candy stripes", "amigurumi", "brick", "chain pattern", "amethyst", "bronze", "chainmail"]

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
        ARTISTS: {ARTISTS}
        CAMERA_ANGLES: {CAMERA_ANGLES}
        COLORS: {COLORS}
        TEXTURES: {TEXTURES}
        I want you to write me 5 detailed prompts using several of the above categories. Use as many words from the lists as you find relevant. In the prompt, describe the scene, and follow by adding only relevant modifiers words from the lists divided by commas to alter the mood, style, lighting, and more.
        Here is the idea you have to work on:
        </END OF SYSTEM PROMPT>"""}