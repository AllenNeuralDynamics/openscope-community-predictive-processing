using Bonsai;
using System;
using System.ComponentModel;
using System.Collections.Generic;
using System.Linq;
using System.Reactive.Linq;
using MathNet.Numerics.Distributions;
using MathNet.Numerics;
using MathNet.Numerics.Interpolation;

[Combinator]
[Description("Creates a lookup table for gamma correction using linear interpolation")]
[WorkflowElementCategory(ElementCategory.Transform)]
public class CreateGammaLookup
{
    public IObservable<double[]> Process(IObservable<Tuple<float, double>[]> source)
    {
        return source.Select(value =>
        {
            var x = Generate.Map(value, v => v.Item2);
            var y = Generate.Map(value, v => (double)v.Item1);
            var vmax = MathNet.Numerics.Statistics.ArrayStatistics.Maximum(y);
            var vmin = MathNet.Numerics.Statistics.ArrayStatistics.Minimum(y);

            // Linear interpolation instead of polynomial
            var linearInterp = Interpolate.Linear(y, x);
            return Generate.Map(x, v => Math.Max(0, linearInterp.Interpolate(v * (vmax - vmin) + vmin)));
        });
    }
}