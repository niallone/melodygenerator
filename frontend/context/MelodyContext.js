import { createContext, useContext, useState } from 'react';

/**
 * MelodyContext is used to share melody-related state across components
 * without having to pass props manually at every level.
 */
const MelodyContext = createContext();

/**
 * MelodyProvider component that wraps the app and provides melody context.
 * It manages the state of generated melodies and provides a function to add new melodies.
 * 
 * @component
 * @param {Object} props - The component props
 * @param {React.ReactNode} props.children - The child components
 * @returns {JSX.Element} The provider component
 *
 * @example
 * <MelodyProvider>
 *   <App />
 * </MelodyProvider>
 */
export function MelodyProvider({ children }) {
  // State to store all generated melodies
  const [melodies, setMelodies] = useState([]);

  /**
   * Function to add a new melody to the state
   * 
   * @param {Object} melody - The melody object to add
   * @param {string} melody.id - Unique identifier for the melody
   * @param {string} melody.name - Name of the melody
   * @param {string} melody.url - URL to access the melody file
   */
  const addMelody = (melody) => {
    setMelodies((prevMelodies) => [...prevMelodies, melody]);
  };

  // The value object that will be shared with all children components
  const value = { melodies, addMelody };

  return (
    <MelodyContext.Provider value={value}>
      {children}
    </MelodyContext.Provider>
  );
}

/**
 * Custom hook to use the melody context
 * 
 * @returns {Object} The melody context value
 * @property {Array} melodies - Array of generated melodies
 * @property {function} addMelody - Function to add a new melody
 *
 * @example
 * const { melodies, addMelody } = useMelodyContext();
 */
export function useMelodyContext() {
  return useContext(MelodyContext);
}