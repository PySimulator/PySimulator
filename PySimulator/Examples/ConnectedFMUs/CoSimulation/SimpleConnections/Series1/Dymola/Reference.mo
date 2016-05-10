within ;
model Reference "Reference solution in pure Modelica"
  extends Modelica.Icons.Example;
  Modelica.Blocks.Sources.Sine sine(amplitude=1, freqHz=2)
    annotation (Placement(transformation(extent={{-60,0},{-40,20}})));
  Modelica.Blocks.Math.Gain gain1(k=2)
    annotation (Placement(transformation(extent={{-20,0},{0,20}})));
  Modelica.Blocks.Math.Gain gain2(k=3)
    annotation (Placement(transformation(extent={{20,0},{40,20}})));
equation
  connect(sine.y, gain1.u) annotation (Line(
      points={{-39,10},{-22,10}},
      color={0,0,127},
      smooth=Smooth.None));
  connect(gain1.y, gain2.u) annotation (Line(
      points={{1,10},{18,10}},
      color={0,0,127},
      smooth=Smooth.None));
  annotation (Diagram(coordinateSystem(preserveAspectRatio=false, extent={{-100,
            -100},{100,100}}), graphics), experiment(StopTime=1.1),
    uses(Modelica(version="3.2.1")));
end Reference;
