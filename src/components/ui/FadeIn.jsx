import React from 'react';
import { motion } from 'framer-motion';

export const FadeIn = ({
  children,
  direction = 'up',
  delay = 0,
  duration = 0.8,
  fullWidth = false,
  className = "",
  ...props
}) => {

  const variants = {
    hidden: {
      opacity: 0,
      y: direction === 'up' ? 25 : direction === 'down' ? -25 : 0,
      x: direction === 'left' ? 25 : direction === 'right' ? -25 : 0,
      scale: direction === 'none' ? 0.97 : 1,
    },
    visible: {
      opacity: 1,
      y: 0,
      x: 0,
      scale: 1,
      transition: {
        duration: duration,
        delay: delay / 1000,
        ease: [0.215, 0.610, 0.355, 1.000], // Custom cubic-bezier for responsive feel
      }
    }
  };

  return (
    <motion.div
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, margin: "-40px" }}
      variants={variants}
      className={`${fullWidth ? 'w-full' : ''} ${className}`}
      {...props}
    >
      {children}
    </motion.div>
  );
};
