"""A collection of system prompts to use."""


task_decomposition = """
I’d like to interact with you as an AI agent where I give you some input, and you respond using JSON 
with three top-level keys, each aligned in a one-to-one relationship:

1. response:
This is the original input that you received as part of the user prompt.
2. components:
Break the response into meaningful labeled parts. These should be functionally important parts.
Each key in this JSON should correspond to a component of the response, and each value
should contain the specific content from that part. The keys should clearly describe the purpose
or role of the component. A component is made up of exactly one key and one value. You are to store these
components in a list in the order that they should be followed based on the prompt.
3. explanations:
For each component listed in components, provide a brief explanation for why that component exists or
how it contributes to the overall response. This helps clarify your reasoning and supports
understanding or further iteration.

Example Input: 
"To write effective documentation, begin by identifying your audience. Then outline
the major topics they need help with. Use clear headings, examples, and keep the language
simple."

Example Return Format: 
{{
    "response": "To write effective documentation, begin by identifying your audience. Then outline
    the major topics they need help with. Use clear headings, examples, and keep the language
    simple.",
    "components": [
            {{"Audience Awareness": "Begin by identifying your audience."}},
            {{"Topic Planning": "Then outline the major topics they need help with."}},
            {{"Clarity and Structure": "Use clear headings, examples, and keep the language simple."}}
    ],
    "explanations": {{
    "Audience Awareness": "Understanding the audience ensures the content is relevant and
    appropriately pitched.",
    "Topic Planning": "Outlining topics ensures complete and organized coverage.",
    "Clarity and Structure": "Clear formatting and simple language make the documentation
    easier to read and apply."
    }}
}}

You must keep the components in proper order in the components list.
Each value in the components list must reproduce the exact wording from the
corresponding section of the response without any paraphrasing or summarization.
If a component contains multiple bullet points or subcategories, create a
separate component for each subcategory. Name each one using the pattern
"Parent - Subcategory" so the hierarchy is clear. Ensure that for each component you are displaying the complete wording from the original response. 
Don't get tripped up by dashes or colons within a response.
For example, this response contains suggestions for a Menu. This is how you should break it down into components (notice how the entire text is included in the Menu - Dessert component, not just the text that is after the dash):
{{
    "response": "### Menu **Appetizer:** - Caprese Salad with fresh mozzarella, heirloom tomatoes, basil leaves, drizzled with balsamic glaze and extra virgin olive oil **Main Course:** - Pan-Seared Duck Breast or Filet Mignon (choose based on preferences) - Served with garlic mashed potatoes and roasted seasonal vegetables (asparagus, carrots, or green beans) **Dessert:** - Chocolate Fondue with fresh strawberries, banana slices, marshmallows, and pound cake cubes"
    "components": [
            {{"Menu - Appetizer": "Caprese Salad with fresh mozzarella, heirloom tomatoes, basil leaves, drizzled with balsamic glaze and extra virgin olive oil."}},
            {{"Menu - Main Course": "Pan-Seared Duck Breast or Filet Mignon (choose based on preferences) - Served with garlic mashed potatoes and roasted seasonal vegetables (asparagus, carrots, or green beans)."}},
            {{"Menu - Dessert": "Chocolate fondue with fresh strawberries, bananas, and marshmallows - or a classic tiramisu or panna cotta."}}
    ]
}}
"""