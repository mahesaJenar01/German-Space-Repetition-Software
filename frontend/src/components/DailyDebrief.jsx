import React from 'react';
import { useQuizStore } from '../store/quizStore';
import '../styles/DailyDebrief.css';

// A small, reusable component for the star button
const StarButton = ({ item }) => {
  const { toggleStarStatus } = useQuizStore();
  
  const handleStarClick = (e) => {
    e.stopPropagation();
    toggleStarStatus(item.item_key);
  };

  const isStarred = item.is_starred || false;

  return (
    <button
      className={`star-button-debrief ${isStarred ? 'starred' : ''}`}
      onClick={handleStarClick}
      aria-label={isStarred ? 'Unstar this word' : 'Star this word'}
      title={isStarred ? 'Unstar this word' : 'Star this word'}
    >
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
        <path d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z" />
      </svg>
    </button>
  );
};

const DailyDebrief = () => {
  const { debriefData, level } = useQuizStore();

  if (!debriefData) {
    return <p>Loading your summary...</p>;
  }

  const { mastered, progress, tricky } = debriefData;

  const renderWordList = (words, category) => (
    <div className={`debrief-category ${category}`}>
      <h2>
        {category === 'mastered' && '✅ Mastered Today'}
        {category === 'progress' && '📈 Making Progress'}
        {category === 'tricky' && '🧠 Tricky Words'}
      </h2>
      <p className="category-description">
        {category === 'mastered' && 'You got these right every time. Great job!'}
        {category === 'progress' && 'You corrected your mistakes on these. That\'s how you learn!'}
        {category === 'tricky' && 'These need a bit more practice. Star them for extra review!'}
      </p>
      {words.length === 0 ? (
        <p className="no-words-message">None in this category today.</p>
      ) : (
        <ul className="debrief-list">
          {words.map((item) => (
            <li key={item.item_key} className="debrief-item">
              <div className="word-info">
                <span className="word-german">{item.word}</span>
                <span className="word-meaning">{item.meaning}</span>
              </div>
              {category === 'tricky' && <StarButton item={item} />}
            </li>
          ))}
        </ul>
      )}
    </div>
  );

  return (
    <div className="daily-debrief-container">
      <h1>Daily Debrief for {level.toUpperCase()}</h1>
      {renderWordList(tricky, 'tricky')}
      {renderWordList(progress, 'progress')}
      {renderWordList(mastered, 'mastered')}
    </div>
  );
};

export default DailyDebrief;