import React, { useEffect, useRef } from 'react';

const ReactiveBackground = () => {
  const canvasRef = useRef(null);
  const mouseRef = useRef({ x: 0, y: 0 });

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    let animationFrameId;

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };

    const onMouseMove = (e) => {
      mouseRef.current = { x: e.clientX, y: e.clientY };
    };

    window.addEventListener('resize', resize);
    window.addEventListener('mousemove', onMouseMove);
    resize();

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      const dotSpacing = 40;
      const dotSize = 1;
      const mouseInfluence = 15;

      for (let x = 0; x < canvas.width; x += dotSpacing) {
        for (let y = 0; y < canvas.height; y += dotSpacing) {
          const dx = x - mouseRef.current.x;
          const dy = y - mouseRef.current.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          
          let offsetX = 0;
          let offsetY = 0;

          if (dist < 300) {
            const force = (300 - dist) / 300;
            offsetX = (dx / dist) * force * mouseInfluence;
            offsetY = (dy / dist) * force * mouseInfluence;
          }

          ctx.fillStyle = dist < 200 ? 'rgba(255, 255, 255, 0.3)' : 'rgba(255, 255, 255, 0.08)';
          ctx.beginPath();
          ctx.arc(x + offsetX, y + offsetY, dotSize, 0, Math.PI * 2);
          ctx.fill();
        }
      }

      animationFrameId = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      window.removeEventListener('resize', resize);
      window.removeEventListener('mousemove', onMouseMove);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <div className="dot-bg-container">
      <canvas ref={canvasRef} />
    </div>
  );
};

export default ReactiveBackground;
