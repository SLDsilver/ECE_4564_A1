import ServerKeys
from watson_developer_cloud import TextToSpeechV1

def request(fname, str):
    text_to_speech = TextToSpeechV1(
        iam_apikey = ServerKeys.WATSON_KEY,
        url='https://gateway-wdc.watsonplatform.net/text-to-speech/api'
        )

    with open(fname, 'wb') as audio_file:
        audio_file.write(text_to_speech.synthesize(str,'audio/wav','en-US_AllisonVoice').get_result().content)
    
if __name__ == "__main__":
    request('test_response.wav',str)
