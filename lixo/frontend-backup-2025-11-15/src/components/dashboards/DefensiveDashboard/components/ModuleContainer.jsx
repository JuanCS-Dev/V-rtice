/**
 * Module Container
 * Wrapper for module content with animations
 */

import React from "react";

const ModuleContainer = ({ children }) => {
  return (
    <div
      style={{
        height: "100%",
        animation: "fade-in 0.3s ease-out",
      }}
    >
      {children}
    </div>
  );
};

export default ModuleContainer;
