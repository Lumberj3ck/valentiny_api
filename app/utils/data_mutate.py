def transform_sections(sections):
    for section in sections:
        if hasattr(section, "__dict__"):
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


def reset_sections_state_with_id(sections):
    sections_list = []
    for section in sections:
        section_data = sections[section]
        modified_image_inputs = [
            section_data["image_inputs"][image_index]
            for image_index in section_data["image_inputs"]
        ]
        modified_text_inputs = [
            section_data["text_inputs"][image_index]
            for image_index in section_data["text_inputs"]
        ]
        section_data["text_inputs"] = modified_text_inputs
        section_data["image_inputs"] = modified_image_inputs

        sections_list.append(section_data)
    return sections_list


def reset_sections_state(sections):
    sections_list = []
    for section in sections:
        section_data = sections[section]
        modified_image_inputs = [
            section_data["image_inputs"][image_index]
            for image_index in section_data["image_inputs"]
        ]
        modified_text_inputs = [
            section_data["text_inputs"][image_index]
            for image_index in section_data["text_inputs"]
        ]
        for image in modified_image_inputs:
            image.pop("id")
        for text in modified_text_inputs:
            text.pop("id")
        section_data["text_inputs"] = modified_text_inputs
        section_data["image_inputs"] = modified_image_inputs
        section_data.pop("id")

        sections_list.append(section_data)
    return sections_list
