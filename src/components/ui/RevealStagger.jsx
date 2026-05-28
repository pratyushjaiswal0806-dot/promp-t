import React from 'react';
import { motion } from 'framer-motion';

export const RevealStagger = ({
    children,
    stagger = 0.08,
    className = "",
    ...props
}) => {
    const containerVariants = {
        hidden: { opacity: 0 },
        visible: {
            opacity: 1,
            transition: {
                staggerChildren: stagger,
                delayChildren: 0.05
            }
        }
    };

    const itemVariants = {
        hidden: { opacity: 0, y: 15 },
        visible: {
            opacity: 1,
            y: 0,
            transition: {
                duration: 0.6,
                ease: [0.215, 0.610, 0.355, 1.000]
            }
        }
    };

    // Filter out falsy children to avoid mapping errors
    const validChildren = React.Children.toArray(children).filter(Boolean);

    return (
        <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-40px" }}
            variants={containerVariants}
            className={className}
            {...props}
        >
            {validChildren.map((child, i) => (
                <motion.div key={i} variants={itemVariants} style={{ display: 'contents' }}>
                    {child}
                </motion.div>
            ))}
        </motion.div>
    );
};
