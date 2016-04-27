within ;
model Reference "Reference solution in pure Modelica"
  extends Modelica.Icons.Example;
  Modelica.Blocks.Continuous.FirstOrder firstOrder1(initType=Modelica.Blocks.Types.Init.InitialState,
      T=0.2) annotation (Placement(transformation(extent={{-20,0},{0,20}})));
  Modelica.Blocks.Continuous.FirstOrder firstOrder2(
    k=1.2,
    initType=Modelica.Blocks.Types.Init.SteadyState,
    T=0.1) annotation (Placement(transformation(extent={{20,0},{40,20}})));
  Modelica.Blocks.Sources.Step step
    annotation (Placement(transformation(extent={{-60,0},{-40,20}})));
equation
  connect(firstOrder1.y, firstOrder2.u) annotation (Line(
      points={{1,10},{18,10}},
      color={0,0,127},
      smooth=Smooth.None));
  connect(step.y, firstOrder1.u) annotation (Line(
      points={{-39,10},{-22,10}},
      color={0,0,127},
      smooth=Smooth.None));
  annotation (Diagram(coordinateSystem(preserveAspectRatio=false, extent={{-100,
            -100},{100,100}}), graphics), experiment(StopTime=1.1),
    uses(Modelica(version="3.2.1")));
end Reference;
