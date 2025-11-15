import { useState, useEffect } from "react";

/**
 * Custom hook for detecting keyboard key presses
 *
 * @param {string} targetKey - The key to listen for
 * @returns {boolean} - Whether the key is currently pressed
 *
 * @example
 * const escapePressed = useKeyPress('Escape');
 * const enterPressed = useKeyPress('Enter');
 *
 * useEffect(() => {
 *   if (escapePressed) {
 *     closeModal();
 *   }
 * }, [escapePressed]);
 */
export const useKeyPress = (targetKey) => {
  const [keyPressed, setKeyPressed] = useState(false);

  useEffect(() => {
    const downHandler = ({ key }) => {
      if (key === targetKey) {
        setKeyPressed(true);
      }
    };

    const upHandler = ({ key }) => {
      if (key === targetKey) {
        setKeyPressed(false);
      }
    };

    window.addEventListener("keydown", downHandler);
    window.addEventListener("keyup", upHandler);

    return () => {
      window.removeEventListener("keydown", downHandler);
      window.removeEventListener("keyup", upHandler);
    };
  }, [targetKey]);

  return keyPressed;
};

export default useKeyPress;
