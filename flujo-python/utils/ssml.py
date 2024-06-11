def make_ssml(text, lang):
    return f'''<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-US'>
        <voice name="en-US-AvaMultilingualNeural">
            <lang xml:lang='{lang}'>
            {text}
            </lang>
        </voice>
    </speak>'''