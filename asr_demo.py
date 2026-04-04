
from funasr import AutoModel

model = AutoModel(
    model="paraformer-zh",
    vad_model="fsmn-vad",
    punc_model="ct-punc",
    vad_kwargs={"max_single_segment_time": 30000},
)

res = model.generate(
    input="https://image-url-2-feature-1251524319.cos.ap-shanghai.myqcloud.com/zailin/datasets/temp/asr_test.wav", 
    sentence_timestamp=True
)
print(res)


###################
# from faster_whisper import WhisperModel

# model = WhisperModel("base", device="cpu", compute_type="int8")

# segments, info = model.transcribe("https://image-url-2-feature-1251524319.cos.ap-shanghai.myqcloud.com/zailin/datasets/temp/asr_test.wav")

# for seg in segments:
#     print(seg.start, seg.end, seg.text)

###############
# import whisperx

# model = whisperx.load_model("base", device="cpu")

# result = model.transcribe("https://image-url-2-feature-1251524319.cos.ap-shanghai.myqcloud.com/zailin/datasets/temp/asr_test.wav")

# model_a, metadata = whisperx.load_align_model(language_code="zh", device="cpu")

# result = whisperx.align(result["segments"], model_a, metadata, "https://image-url-2-feature-1251524319.cos.ap-shanghai.myqcloud.com/zailin/datasets/temp/asr_test.wav", device="cpu")
# print(result)