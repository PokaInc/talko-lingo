import uuid


def build_job_id(input_device_id, input_lang, output_device_id, output_lang):
    return '{unique_id}.{input_device_id}.{input_lang}.{output_device_id}.{output_lang}'.format(
        unique_id=str(uuid.uuid4()),
        input_device_id=input_device_id,
        input_lang=input_lang,
        output_device_id=output_device_id,
        output_lang=output_lang,
    )


def extract_input_output_lang_from_job_id(job_id):
    parts = job_id.split('.')
    input_lang = parts[2]
    output_lang = parts[4]

    return input_lang, output_lang


def extract_output_device_from_job_id(job_id):
    parts = job_id.split('.')
    output_device_id = parts[3]

    return output_device_id
