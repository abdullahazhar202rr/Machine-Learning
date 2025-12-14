import { useEffect, useRef } from 'react';
import cloud from 'd3-cloud';

interface WordCloudProps {
  data: Record<string, number>;
}

export function WordCloud({ data }: WordCloudProps) {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current || Object.keys(data).length === 0) return;

    const words = Object.entries(data).map(([text, size]) => ({
      text,
      size: Math.sqrt(size) * 15 + 10,
    }));

    const width = svgRef.current.clientWidth;
    const height = 400;

    const layout = cloud()
      .size([width, height])
      .words(words)
      .padding(5)
      .rotate(() => (Math.random() > 0.5 ? 0 : 90))
      .fontSize((d: any) => d.size)
      .on('end', draw);

    layout.start();

    function draw(words: any[]) {
      if (!svgRef.current) return;

      svgRef.current.innerHTML = '';

      const svg = svgRef.current;
      const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      g.setAttribute('transform', `translate(${width / 2},${height / 2})`);

      words.forEach((word) => {
        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.style.fontSize = `${word.size}px`;
        text.style.fontFamily = 'Inter, system-ui, sans-serif';
        text.style.fontWeight = '600';
        text.style.fill = `hsl(${Math.random() * 60 + 200}, 70%, 50%)`;
        text.setAttribute('text-anchor', 'middle');
        text.setAttribute(
          'transform',
          `translate(${word.x},${word.y})rotate(${word.rotate})`
        );
        text.textContent = word.text;
        g.appendChild(text);
      });

      svg.appendChild(g);
    }
  }, [data]);

  if (Object.keys(data).length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-400">
        No keywords available
      </div>
    );
  }

  return (
    <div className="w-full overflow-hidden">
      <svg ref={svgRef} width="100%" height="400" />
    </div>
  );
}
