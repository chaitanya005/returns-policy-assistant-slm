import tinker

service_client = tinker.ServiceClient()
sampling_client = service_client.create_sampling_client(base_model="Qwen/Qwen3-8B")
tokenizer = sampling_client.get_tokenizer()

prompt = tinker.ModelInput.from_ints(tokenizer.encode("The capital of France is"))
params = tinker.SamplingParams(max_tokens=20, temperature=0.0)
result = sampling_client.sample(prompt=prompt, num_samples=1, sampling_params=params).result()
print(tokenizer.decode(result.sequences[0].tokens))
