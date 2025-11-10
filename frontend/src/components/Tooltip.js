import React, { useState, useRef } from 'react';

const Tooltip = ({ children, text, position = 'top', delay = 500 }) => {
  const [isVisible, setIsVisible] = useState(false);
  const [timeoutId, setTimeoutId] = useState(null);
  const [tooltipPosition, setTooltipPosition] = useState({ top: 0, left: 0 });
  const triggerRef = useRef(null);

  const showTooltip = () => {
    const id = setTimeout(() => {
      if (triggerRef.current) {
        const rect = triggerRef.current.getBoundingClientRect();
        const scrollX = window.pageXOffset || document.documentElement.scrollLeft;
        const scrollY = window.pageYOffset || document.documentElement.scrollTop;
        
        let top, left;
        switch (position) {
          case 'top':
            top = rect.top + scrollY - 20;
            left = rect.left + scrollX + rect.width / 2;
            break;
          case 'bottom':
            top = rect.bottom + scrollY + 20;
            left = rect.left + scrollX + rect.width / 2;
            break;
          case 'left':
            top = rect.top + scrollY + rect.height / 2;
            left = rect.left + scrollX - 20;
            break;
          case 'right':
            top = rect.top + scrollY + rect.height / 2;
            left = rect.right + scrollX + 20;
            break;
          default:
            top = rect.top + scrollY - 20;
            left = rect.left + scrollX + rect.width / 2;
        }
        
        setTooltipPosition({ top, left });
      }
      setIsVisible(true);
    }, delay);
    setTimeoutId(id);
  };

  const hideTooltip = () => {
    if (timeoutId) {
      clearTimeout(timeoutId);
      setTimeoutId(null);
    }
    setIsVisible(false);
  };

  const getTooltipStyles = () => {
    const baseStyles = {
      position: 'fixed',
      background: '#1f2937',
      color: 'white',
      padding: '6px 10px',
      borderRadius: '6px',
      fontSize: '12px',
      fontWeight: '500',
      whiteSpace: 'nowrap',
      zIndex: 9999,
      pointerEvents: 'none',
      boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
      border: '1px solid rgba(255, 255, 255, 0.1)',
      backdropFilter: 'blur(8px)',
      opacity: isVisible ? 1 : 0,
      transform: isVisible ? 'scale(1)' : 'scale(0.95)',
      transition: 'all 0.15s cubic-bezier(0.4, 0, 0.2, 1)',
    };


    switch (position) {
      case 'top':
        return {
          ...baseStyles,
          top: tooltipPosition.top,
          left: tooltipPosition.left,
          transform: isVisible 
            ? 'translateX(-50%) translateY(-8px) scale(1)' 
            : 'translateX(-50%) translateY(-4px) scale(0.95)',
        };
      case 'bottom':
        return {
          ...baseStyles,
          top: tooltipPosition.top,
          left: tooltipPosition.left,
          transform: isVisible 
            ? 'translateX(-50%) translateY(8px) scale(1)' 
            : 'translateX(-50%) translateY(4px) scale(0.95)',
        };
      case 'left':
        return {
          ...baseStyles,
          top: tooltipPosition.top,
          left: tooltipPosition.left,
          transform: isVisible 
            ? 'translateX(-8px) translateY(-50%) scale(1)' 
            : 'translateX(-4px) translateY(-50%) scale(0.95)',
        };
      case 'right':
        return {
          ...baseStyles,
          top: tooltipPosition.top,
          left: tooltipPosition.left,
          transform: isVisible 
            ? 'translateX(8px) translateY(-50%) scale(1)' 
            : 'translateX(4px) translateY(-50%) scale(0.95)',
        };
      default:
        return {
          ...baseStyles,
          top: tooltipPosition.top,
          left: tooltipPosition.left,
          transform: isVisible 
            ? 'translateX(-50%) translateY(-8px) scale(1)' 
            : 'translateX(-50%) translateY(-4px) scale(0.95)',
        };
    }
  };

  return (
    <>
      <div 
        ref={triggerRef}
        style={{ position: 'relative', display: 'inline-block' }}
        onMouseEnter={showTooltip}
        onMouseLeave={hideTooltip}
      >
        {children}
      </div>
      {isVisible && (
        <div style={getTooltipStyles()}>
          {text}
          {position === 'top' && (
            <div
              style={{
                position: 'absolute',
                top: '100%',
                left: '50%',
                marginLeft: '-4px',
                width: 0,
                height: 0,
                borderStyle: 'solid',
                borderWidth: '4px 4px 0 4px',
                borderColor: '#1f2937 transparent transparent transparent',
              }}
            />
          )}
        </div>
      )}
    </>
  );
};

export default Tooltip;
