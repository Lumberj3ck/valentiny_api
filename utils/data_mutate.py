def transform_sections(sections):
    for section in sections:
        section = section.__dict__
        modified_text_inputs = {
            text_input.index: text_input for text_input in section.get("text_inputs")
        }
        modified_image_inputs = {
            image_input.index: image_input
            for image_input in section.get("image_inputs")
        }
        section["text_inputs"] = modified_text_inputs
        section["image_inputs"] = modified_image_inputs

    sections_dict = {section.name: section for section in sections}
    return sections_dict




