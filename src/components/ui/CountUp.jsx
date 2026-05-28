import React, { useEffect, useRef } from 'react';
import { useInView, useMotionValue, useSpring } from 'framer-motion';

export const CountUp = ({
    end,
    suffix = "",
    duration = 2,
    className = "",
    decimals = 0
}) => {
    const ref = useRef(null);
    const motionValue = useMotionValue(0);
    const springValue = useSpring(motionValue, {
        damping: 30,
        stiffness: 100,
        duration: duration * 1000
    });
    const isInView = useInView(ref, { once: true, margin: "-10px" });

    useEffect(() => {
        if (isInView) {
            motionValue.set(end);
        }
    }, [isInView, end, motionValue]);

    useEffect(() => {
        const unsubscribe = springValue.on("change", (latest) => {
            if (ref.current) {
                ref.current.textContent = latest.toFixed(decimals) + suffix;
            }
        });
        return () => unsubscribe();
    }, [springValue, decimals, suffix]);

    return <span ref={ref} className={className}>0{suffix}</span>;
};
