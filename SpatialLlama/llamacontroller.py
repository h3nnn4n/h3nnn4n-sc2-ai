import random


class LlamaControler:
    def __init__(self):
        self.messages = [
                'Llamas are members of the camelid, or camel, family.,',
                'Llamas were first domesticated and used as pack animals 4,000 to 5,000 years ago by Indians in the Peruvian highlands.',
                'Llamas can grow as much as 6 feet tall.',
                'Llamas are hardy and well suited to harsh environments.',
                'Llamas are smart and easy to train.',
                'Llamas are vegetarians and have efficient digestive systems.',
                'Llamas live to be about 20 years old.',
                'Llamas dont bite. They spit when theyre agitated, but thats mostly at each other.',
                'Llamas typically live for 15 to 25 years, with some individuals surviving 30 years or more.',
                'Llamas typically live for 15 to 25 years, with some individuals surviving 30 years or more.',
                'Llama’s have an excellent sense of smell, eyesight and hearing.',
                'Llamas can reach speeds up to 56 kilometer (35 miles) per hour.',
                'Llamas are a very gentle, shy and a very curious animal.',
                'Llamas are also intelligent and can learn simple tasks after a few repetitions.',
                'Llamas have 3 stomach compartments and they chew their cud. Cud is a mouthful of swallowed food that is regurgitated from the first stomach.',
                'Llamas do not have specific time of mating.',
                'Some ranchers and farmers use “guard llamas” to safeguard their sheep or other livestock.',
            ]

    def get_random_llama_fact(self):
        return random.sample(self.messages, k=1)[0]
