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


export const createQuizItems = (meaningDetailsList, wordsStats) => {
  return meaningDetailsList.map(meaningDetail => {
    const itemKey = meaningDetail.item_key;
    const stats = wordsStats[itemKey] || {};
    // fullWordData now correctly contains both details and stats (like is_starred)
    const fullWordData = { ...meaningDetail, ...stats };
    
    let direction;
    const isNounWithArticleErrors = meaningDetail.type === 'Nomen' && fullWordData.article_wrong > 0;

    if (isNounWithArticleErrors) {
      direction = 'meaningToWord';
    } else {
      direction = Math.random() > 0.5 ? 'wordToMeaning' : 'meaningToWord';
    }

    const isWordToMeaning = direction === 'wordToMeaning';

    return {
      key: itemKey,
      question: isWordToMeaning ? fullWordData.word : fullWordData.meaning,
      correctAnswers: isWordToMeaning ? generateWordToMeaningAnswers(fullWordData) : generateMeaningToWordAnswers(fullWordData),
      displayAnswer: isWordToMeaning ? fullWordData.meaning : fullWordData.word,
      direction: direction,
      article_wrong: fullWordData.article_wrong || 0,
      // Assign the merged object to fullDetails so 'is_starred' is available
      fullDetails: fullWordData,
    };
  });
};

// This function takes quiz items that are MISSING data and re-adds them.
export const rehydrateQuizAnswers = (sanitizedQuizItems, allWordsDetails) => {
  // Create a fast lookup map from item_key to its full details object
  const detailsMap = allWordsDetails.reduce((acc, detail) => {
    acc[detail.item_key] = detail;
    return acc;
  }, {});

  return sanitizedQuizItems.map(item => {
    // item.key is the item_key
    const fullWordData = detailsMap[item.key];
    if (!fullWordData) return item; // Safeguard

    const isWordToMeaning = item.direction === 'wordToMeaning';
    const correctAnswers = isWordToMeaning 
      ? generateWordToMeaningAnswers(fullWordData) 
      : generateMeaningToWordAnswers(fullWordData);
      
    return {
      ...item,
      correctAnswers, // Add the answers back
      fullDetails: fullWordData, 
    };
  });
};