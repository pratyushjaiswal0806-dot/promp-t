import React, { useRef } from 'react';
import { motion, useScroll, useTransform } from 'framer-motion';

export const ParallaxImage = ({
    src,
    alt,
    className = "",
    strength = 40
}) => {
    const ref = useRef(null);
    const { scrollYProgress } = useScroll({
        target: ref,
        offset: ["start end", "end start"]
    });

    const y = useTransform(scrollYProgress, [0, 1], [-strength, strength]);

    return (
        <div ref={ref} className={`overflow-hidden ${className}`} style={{ position: 'relative' }}>
            <motion.img
                src={src}
                alt={alt}
                style={{ y, position: 'absolute', top: '-10%', left: 0, width: '100%', height: '120%' }}
                className="object-cover"
            />
        </div>
    );
};
