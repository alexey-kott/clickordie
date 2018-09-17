import re


def is_trash(msg_text):
	msg_text = msg_text.lower()

	# если алиасов больше 4-х, то скорее всего это подборка каналов
	if len(count_aliases(msg_text)) > 4: 
		return True

	# спам-слова
	trash = ['подписыва', 'подписаться']
	for word in trash:
		if msg_text.find(word) != -1:
			return True

	return False


def count_aliases(msg_text):
	aliases = re.findall(r'@[\S]+', msg_text)

	return len(aliases)
