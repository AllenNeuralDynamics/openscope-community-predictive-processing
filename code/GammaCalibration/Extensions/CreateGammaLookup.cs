using Bonsai;
using System;
using System.ComponentModel;
using System.Collections.Generic;
using System.Linq;
using System.Reactive.Linq;
using MathNet.Numerics.Distributions;
using MathNet.Numerics;

[Combinator]
[Description("")]
[WorkflowElementCategory(ElementCategory.Transform)]
public class CreateGammaLookup
{
    public IObservable<double[]> Process(IObservable<Tuple<float, double>[]> source)
    {
        return source.Select(value =>
        {
            var x = Generate.Map(value, v => v.Item2);
            var y = Generate.Map(value, v => (double)v.Item1);

            // var p = Fit.LogarithmFunc(y, x);
            var p = Fit.PolynomialFunc(y, x, 6);
            var vmax = MathNet.Numerics.Statistics.ArrayStatistics.Maximum(y);

            // var p = Fit.Logarithm(y, x);
            //  return  Generate.Map(x, v => p.Item1 + p.Item2 * Math.Log(v));  
            return Generate.Map(x, v => Math.Max(0, p(v * vmax)));
        });
    }
}
