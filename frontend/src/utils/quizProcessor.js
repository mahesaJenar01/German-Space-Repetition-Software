const generateWordToMeaningAnswers = (fullWordData) => {
  const meaningStr = fullWordData.meaning.trim().toLowerCase();
  const correctAnswersSet = new Set([meaningStr]);
  const withoutParentheses = meaningStr.replace(/\s*\(.*?\)\s*/g, '').trim();
  if (withoutParentheses && withoutParentheses !== meaningStr) {
    correctAnswersSet.add(withoutParentheses);
  }
  const parts = meaningStr.split(';').map(p => p.trim()).filter(Boolean);
  if (parts.length > 1) {
    parts.forEach(part => {
      correctAnswersSet.add(part);
      const partWithoutParen = part.replace(/\s*\(.*?\)\s*/g, '').trim();
      if (partWithoutParen && partWithoutParen !== part) {
        correctAnswersSet.add(partWithoutParen);
      }
    });
  }
  return Array.from(correctAnswersSet);
};

const generateMeaningToWordAnswers = (fullWordData) => {
  const isNoun = fullWordData.type === 'Nomen';
  const germanWordStr = fullWordData.word.trim();
  const baseAnswers = new Set([germanWordStr]);
  const parts = germanWordStr.split(';').map(p => p.trim()).filter(Boolean);
  if (parts.length > 1) {
    parts.forEach(part => baseAnswers.add(part));
  }
  const finalAnswers = new Set();
  baseAnswers.forEach(answer => {
    const addVariant = (variant) => finalAnswers.add(isNoun ? variant : variant.toLowerCase());
    addVariant(answer);
    if (answer.includes('ß')) addVariant(answer.replace(/ß/g, 'ss'));
    const wordParts = answer.split(' ');
    if (wordParts.length > 1 && ['der', 'die', 'das'].includes(wordParts[0].toLowerCase())) {
      const withoutArticle = wordParts.slice(1).join(' ');
      addVariant(withoutArticle);
      if (withoutArticle.includes('ß')) addVariant(withoutArticle.replace(/ß/g, 'ss'));
    }
  });
  return Array.from(finalAnswers);
};


export const createQuizItems = (wordsDetails, wordsStats) => {
  return wordsDetails.map(wordDetail => {
    const stats = wordsStats[wordDetail.word] || {};
    const fullWordData = { ...wordDetail, ...stats };
    
    let direction;
    const isNounWithArticleErrors = wordDetail.type === 'Nomen' && fullWordData.article_wrong > 0;

    if (isNounWithArticleErrors) {
      // This noun has a history of article mistakes.
      // Force the quiz direction to test the article again.
      direction = 'meaningToWord';
    } else {
      // Default random direction for all other words or nouns without article errors.
      direction = Math.random() > 0.5 ? 'wordToMeaning' : 'meaningToWord';
    }

    const isWordToMeaning = direction === 'wordToMeaning';

    return {
      key: fullWordData.word,
      question: isWordToMeaning ? fullWordData.word : fullWordData.meaning,
      correctAnswers: isWordToMeaning ? generateWordToMeaningAnswers(fullWordData) : generateMeaningToWordAnswers(fullWordData),
      displayAnswer: isWordToMeaning ? fullWordData.meaning : fullWordData.word,
      direction: direction,
      article_wrong: fullWordData.article_wrong || 0,
    };
  });
};

// This function takes quiz items that are MISSING answers and re-adds them.
export const rehydrateQuizAnswers = (sanitizedQuizItems, allWords) => {
  const wordsMap = allWords.reduce((acc, word) => {
    acc[word.word] = word;
    return acc;
  }, {});

  return sanitizedQuizItems.map(item => {
    const fullWordData = wordsMap[item.key];
    if (!fullWordData) return item; // Should not happen, but a good safeguard

    const isWordToMeaning = item.direction === 'wordToMeaning';
    const correctAnswers = isWordToMeaning 
      ? generateWordToMeaningAnswers(fullWordData) 
      : generateMeaningToWordAnswers(fullWordData);
      
    return {
      ...item,
      correctAnswers, // Add the answers back in memory
    };
  });
};