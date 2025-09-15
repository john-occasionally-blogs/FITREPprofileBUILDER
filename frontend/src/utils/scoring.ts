// Frontend utilities for FITREP scoring

export const LETTER_TO_NUMERIC: { [key: string]: number } = {
  'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7
};

export const TRAIT_NAMES = [
  "Mission Accomplishment",
  "Proficiency", 
  "Individual Character",
  "Effectiveness Under Stress",
  "Initiative",
  "Leadership",
  "Developing Subordinates",
  "Setting the Example", 
  "Ensuring Well-being of Subordinates",
  "Communication Skills",
  "Intellect and Wisdom",
  "Decision Making Ability",
  "Judgment",
  "Fulfillment of Evaluation Responsibilities"
];

export const calculateFRAScore = (traitScores: { [key: string]: string }): number | null => {
  const numericScores: number[] = [];
  
  for (const [traitName, letterGrade] of Object.entries(traitScores)) {
    if (letterGrade === 'H') {
      // Non-observed, skip
      continue;
    } else if (letterGrade in LETTER_TO_NUMERIC) {
      numericScores.push(LETTER_TO_NUMERIC[letterGrade]);
    } else {
      console.warn(`Invalid letter grade '${letterGrade}' for trait '${traitName}'`);
      return null;
    }
  }
  
  if (numericScores.length === 0) {
    return null;
  }
  
  const average = numericScores.reduce((sum, score) => sum + score, 0) / numericScores.length;
  return Math.round(average * 100) / 100; // Round to 2 decimal places
};

export const formatRVScore = (rv: number | null): string => {
  if (rv === null || rv === undefined) {
    return 'N/A';
  }
  return rv.toString();
};

export const getRVColor = (rv: number | null): string => {
  if (!rv) return '#6c757d';
  if (rv >= 95) return '#28a745';
  if (rv >= 90) return '#ffc107';
  if (rv >= 85) return '#fd7e14';
  return '#dc3545';
};